from datetime import UTC, datetime, timedelta
from math import floor
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.auth import Database, require_roles
from app.mentoring_capacity import OPEN_RELATIONSHIP_STATUSES, occupied_mentees
from app.mentoring_schemas import (
    AcceptanceResponse,
    MentorBrief,
    RelationshipResponse,
    RelationshipStatusUpdate,
    RequestCreate,
    RequestRejection,
    RequestResponse,
    ResourceId,
    StudentBrief,
)
from app.models import (
    GuidanceArea,
    MentoringRelationship,
    MentoringRequest,
    MentorProfile,
    MentorVerification,
    RelationshipStatus,
    RequestStatus,
    User,
    UserRole,
    mentor_guidance_areas,
)
from app.request_expiry import expire_pending
from app.schemas import ErrorResponse

ROUTE_ERRORS = {
    401: {"model": ErrorResponse, "description": "Authentication required"},
    403: {"model": ErrorResponse, "description": "Role does not allow this action"},
}
request_router = APIRouter(
    prefix="/requests", tags=["Mentoring requests"], responses=ROUTE_ERRORS
)
relationship_router = APIRouter(
    prefix="/relationships", tags=["Mentoring relationships"], responses=ROUTE_ERRORS
)
Participant = Annotated[User, Depends(require_roles(UserRole.STUDENT, UserRole.MENTOR))]
Student = Annotated[User, Depends(require_roles(UserRole.STUDENT))]
Mentor = Annotated[User, Depends(require_roles(UserRole.MENTOR))]
REQUEST_LIFETIME = timedelta(hours=48)


def request_owner(user: User):
    if user.role == UserRole.STUDENT:
        return MentoringRequest.student_id == user.user_id
    return MentoringRequest.mentor_id == user.user_id


def request_parties():
    return (
        joinedload(MentoringRequest.area),
        joinedload(MentoringRequest.student).joinedload(User.student_profile),
        joinedload(MentoringRequest.mentor).joinedload(User.mentor_profile),
    )


def request_query():
    return select(MentoringRequest).options(
        *request_parties(), joinedload(MentoringRequest.mentoring_relationship)
    )


def relationship_query():
    return (
        select(MentoringRelationship)
        .join(MentoringRelationship.request)
        .options(joinedload(MentoringRelationship.request).options(*request_parties()))
    )


def get_relationship(
    db: Session, relationship_id: int, user: User, *, lock: bool = False
) -> MentoringRelationship:
    query = relationship_query().where(
        MentoringRelationship.relationship_id == relationship_id, request_owner(user)
    )
    if lock:
        query = query.with_for_update(of=MentoringRelationship)
    record = db.scalar(query)
    if record is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return record


def participant_profiles(record: MentoringRequest) -> tuple[StudentBrief, MentorBrief]:
    student = record.student.student_profile
    mentor = record.mentor.mentor_profile
    return (
        StudentBrief(
            id=record.student_id,
            name=record.student.name,
            roll_number=student.roll_number if student else None,
            education=student.education if student else None,
            career_stage=student.career_stage if student else None,
            career_objective=student.career_objective if student else None,
        ),
        MentorBrief(
            id=record.mentor_id,
            name=record.mentor.name,
            current_role=mentor.current_role if mentor else None,
            organisation=mentor.organisation if mentor else None,
        ),
    )


def request_response(record: MentoringRequest) -> RequestResponse:
    student, mentor = participant_profiles(record)
    hours_left = None
    if record.status == RequestStatus.PENDING:
        remaining = (record.expires_at - datetime.now(UTC)).total_seconds() / 3600
        hours_left = max(0, floor(remaining + 0.5))
    return RequestResponse(
        id=record.request_id,
        student_id=record.student_id,
        mentor_id=record.mentor_id,
        area_id=record.area_id,
        message=record.message,
        objective=record.objective,
        type=record.type,
        status=record.status,
        created_at=record.created_at,
        expires_at=record.expires_at,
        responded_at=record.responded_at,
        reject_reason=record.reject_reason,
        area=record.area.name,
        student=student,
        mentor=mentor,
        relationship_id=(
            record.mentoring_relationship.relationship_id
            if record.mentoring_relationship
            else None
        ),
        hours_left=hours_left,
    )


def relationship_response(record: MentoringRelationship) -> RelationshipResponse:
    student, mentor = participant_profiles(record.request)
    return RelationshipResponse(
        id=record.relationship_id,
        request_id=record.request_id,
        status=record.status,
        type=record.request.type,
        started_at=record.started_at,
        ended_at=record.ended_at,
        area=record.request.area.name,
        student=student,
        mentor=mentor,
    )


def lock_mentor(db: Session, mentor_id: int) -> MentorProfile:
    # Profile changes take the same account lock before changing capacity or areas.
    account = db.scalar(
        select(User.user_id)
        .where(User.user_id == mentor_id, User.is_active, User.role == UserRole.MENTOR)
        .with_for_update()
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Mentor not found")
    profile = db.scalar(
        select(MentorProfile)
        .where(MentorProfile.user_id == mentor_id)
        .with_for_update()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Mentor not found")
    if profile.verification_status != MentorVerification.VERIFIED:
        raise HTTPException(status_code=409, detail="This mentor is not verified")
    return profile


def check_capacity(db: Session, profile: MentorProfile) -> None:
    if db.scalar(occupied_mentees(profile.user_id)) >= profile.max_mentees:
        raise HTTPException(status_code=409, detail="This mentor is at full capacity")


def pending_request(db: Session, request_id: int, user: User) -> MentoringRequest:
    condition = MentoringRequest.request_id == request_id
    record = db.scalar(
        request_query()
        .where(condition, request_owner(user))
        .with_for_update(of=MentoringRequest)
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Request not found")
    now = datetime.now(UTC)
    if record.status == RequestStatus.PENDING and record.expires_at <= now:
        expire_pending(db, now, condition)
        db.commit()
        raise HTTPException(status_code=409, detail="Request is already expired")
    if record.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=409, detail=f"Request is already {record.status.value.lower()}"
        )
    return record


@request_router.post(
    "",
    status_code=201,
    responses={
        404: {"model": ErrorResponse, "description": "Mentor not found"},
        409: {
            "model": ErrorResponse,
            "description": "Mentor unavailable or request already pending",
        },
    },
)
def create_request(data: RequestCreate, user: Student, db: Database) -> RequestResponse:
    profile = lock_mentor(db, data.mentor_id)
    if not profile.is_accepting:
        raise HTTPException(
            status_code=409, detail="This mentor is not accepting requests"
        )
    check_capacity(db, profile)
    offered_area = db.scalar(
        select(GuidanceArea)
        .join(mentor_guidance_areas)
        .where(
            mentor_guidance_areas.c.mentor_profile_id == profile.profile_id,
            GuidanceArea.area_id == data.area_id,
            GuidanceArea.is_active,
        )
        .with_for_update(read=True, of=GuidanceArea)
    )
    if offered_area is None:
        raise HTTPException(
            status_code=422,
            detail="This mentor does not offer the selected active guidance area",
        )
    now = datetime.now(UTC)
    expire_pending(
        db,
        now,
        MentoringRequest.student_id == user.user_id,
        MentoringRequest.mentor_id == data.mentor_id,
    )
    record = MentoringRequest(
        student_id=user.user_id,
        mentor_id=data.mentor_id,
        area=offered_area,
        message=data.message,
        objective=data.objective,
        type=data.type,
        created_at=now,
        expires_at=now + REQUEST_LIFETIME,
    )
    db.add(record)
    try:
        db.flush()
    except IntegrityError as error:
        db.rollback()
        if error.orig.diag.constraint_name == "uq_pending_request_pair":
            raise HTTPException(
                status_code=409,
                detail="You already have a pending request to this mentor",
            ) from None
        raise
    response = request_response(record)
    db.commit()
    return response


@request_router.get("")
def list_requests(
    user: Participant, db: Database, status: RequestStatus | None = None
) -> list[RequestResponse]:
    """Return the student's outbox or the mentor's inbox."""
    owner = request_owner(user)
    expired = expire_pending(db, datetime.now(UTC), owner)
    query = request_query().where(owner)
    if status is not None:
        query = query.where(MentoringRequest.status == status)
    result = [
        request_response(row)
        for row in db.scalars(
            query.order_by(
                MentoringRequest.created_at.desc(), MentoringRequest.request_id.desc()
            )
        )
    ]
    if expired:
        db.commit()
    return result


@request_router.get(
    "/{request_id}",
    responses={404: {"model": ErrorResponse, "description": "Request not found"}},
)
def read_request(
    request_id: ResourceId, user: Participant, db: Database
) -> RequestResponse:
    conditions = (MentoringRequest.request_id == request_id, request_owner(user))
    expired = expire_pending(db, datetime.now(UTC), *conditions)
    record = db.scalar(request_query().where(*conditions))
    if record is None:
        raise HTTPException(status_code=404, detail="Request not found")
    response = request_response(record)
    if expired:
        db.commit()
    return response


REQUEST_ACTION_ERRORS = {
    404: {"model": ErrorResponse, "description": "Request not found"},
    409: {"model": ErrorResponse, "description": "Request cannot change state"},
}


@request_router.post("/{request_id}/accept", responses=REQUEST_ACTION_ERRORS)
def accept_request(
    request_id: ResourceId, user: Mentor, db: Database
) -> AcceptanceResponse:
    profile = lock_mentor(db, user.user_id)
    record = pending_request(db, request_id, user)
    check_capacity(db, profile)
    now = datetime.now(UTC)
    record.status = RequestStatus.ACCEPTED
    record.responded_at = now
    relationship = MentoringRelationship(request=record, started_at=now)
    db.add(relationship)
    db.flush()
    response = AcceptanceResponse(
        request=request_response(record),
        relationship=relationship_response(relationship),
    )
    db.commit()
    return response


@request_router.post("/{request_id}/reject", responses=REQUEST_ACTION_ERRORS)
def reject_request(
    request_id: ResourceId,
    user: Mentor,
    db: Database,
    data: RequestRejection | None = None,
) -> RequestResponse:
    record = pending_request(db, request_id, user)
    record.status = RequestStatus.REJECTED
    record.responded_at = datetime.now(UTC)
    record.reject_reason = (data.reason or None) if data else None
    response = request_response(record)
    db.commit()
    return response


@request_router.post("/{request_id}/cancel", responses=REQUEST_ACTION_ERRORS)
def cancel_request(
    request_id: ResourceId, user: Student, db: Database
) -> RequestResponse:
    record = pending_request(db, request_id, user)
    record.status = RequestStatus.CANCELLED
    record.responded_at = datetime.now(UTC)
    response = request_response(record)
    db.commit()
    return response


@relationship_router.get("")
def list_relationships(
    user: Participant, db: Database, status: RelationshipStatus | None = None
) -> list[RelationshipResponse]:
    query = relationship_query().where(request_owner(user))
    if status is not None:
        query = query.where(MentoringRelationship.status == status)
    return [
        relationship_response(row)
        for row in db.scalars(
            query.order_by(
                MentoringRelationship.started_at.desc(),
                MentoringRelationship.relationship_id.desc(),
            )
        )
    ]


@relationship_router.get(
    "/{relationship_id}",
    responses={404: {"model": ErrorResponse, "description": "Relationship not found"}},
)
def read_relationship(
    relationship_id: ResourceId, user: Participant, db: Database
) -> RelationshipResponse:
    return relationship_response(get_relationship(db, relationship_id, user))


@relationship_router.patch(
    "/{relationship_id}/status",
    responses={
        404: {"model": ErrorResponse, "description": "Relationship not found"},
        409: {"model": ErrorResponse, "description": "Invalid relationship transition"},
    },
)
def update_relationship(
    relationship_id: ResourceId,
    data: RelationshipStatusUpdate,
    user: Participant,
    db: Database,
) -> RelationshipResponse:
    record = get_relationship(db, relationship_id, user, lock=True)
    if record.status not in OPEN_RELATIONSHIP_STATUSES or data.status == record.status:
        raise HTTPException(status_code=409, detail="Invalid relationship transition")
    if data.status == RelationshipStatus.CLOSED and user.role != UserRole.MENTOR:
        raise HTTPException(
            status_code=403, detail="Only the mentor can close a relationship"
        )
    record.status = data.status
    if data.status not in OPEN_RELATIONSHIP_STATUSES:
        record.ended_at = datetime.now(UTC)
    response = relationship_response(record)
    db.commit()
    return response
