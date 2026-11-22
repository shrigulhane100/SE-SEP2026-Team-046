from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.auth import Database
from app.engagement_schemas import (
    ActivityCreate,
    FeedbackList,
    FeedbackListItem,
    FeedbackResponse,
    FeedbackWrite,
    GoalCreate,
    GoalUpdate,
)
from app.mentoring import (
    ROUTE_ERRORS,
    Participant,
    get_relationship,
    other_participant,
    relationship_response,
    request_owner,
)
from app.mentoring_capacity import OPEN_RELATIONSHIP_STATUSES
from app.mentoring_schemas import RelationshipResponse, ResourceId
from app.models import (
    Activity,
    Feedback,
    Goal,
    GuidanceArea,
    MentoringRelationship,
    MentoringRequest,
    NotificationType,
    UserRole,
)
from app.notifications import notify
from app.schemas import ErrorResponse

engagement_router = APIRouter(tags=["Mentoring activity"], responses=ROUTE_ERRORS)
OPEN_RELATIONSHIP_ERRORS = {
    404: {"model": ErrorResponse, "description": "Relationship or goal not found"},
    409: {"model": ErrorResponse, "description": "Relationship is closed or completed"},
}


def require_open(relationship: MentoringRelationship) -> None:
    if relationship.status not in OPEN_RELATIONSHIP_STATUSES:
        raise HTTPException(
            status_code=409, detail="This relationship is no longer open"
        )


@engagement_router.post(
    "/relationships/{relationship_id}/goals",
    status_code=201,
    responses=OPEN_RELATIONSHIP_ERRORS,
)
def create_goal(
    relationship_id: ResourceId, data: GoalCreate, user: Participant, db: Database
) -> RelationshipResponse:
    record = get_relationship(db, relationship_id, user, lock=True)
    require_open(record)
    db.add(Goal(relationship=record, author=user, **data.model_dump()))
    notify(
        db,
        other_participant(record.request, user.user_id),
        NotificationType.GOAL_ADDED,
        f"{user.name} added a goal.",
        record,
    )
    db.flush()
    response = relationship_response(record)
    db.commit()
    return response


@engagement_router.patch("/goals/{goal_id}", responses=OPEN_RELATIONSHIP_ERRORS)
def update_goal(
    goal_id: ResourceId, data: GoalUpdate, user: Participant, db: Database
) -> RelationshipResponse:
    relationship_id = db.scalar(
        select(Goal.relationship_id)
        .join(Goal.relationship)
        .join(MentoringRelationship.request)
        .where(Goal.goal_id == goal_id, request_owner(user))
    )
    if relationship_id is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    record = get_relationship(db, relationship_id, user, lock=True)
    require_open(record)
    goal = next(goal for goal in record.goals if goal.goal_id == goal_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    response = relationship_response(record)
    db.commit()
    return response


@engagement_router.post(
    "/relationships/{relationship_id}/activities",
    status_code=201,
    responses=OPEN_RELATIONSHIP_ERRORS,
)
def record_activity(
    relationship_id: ResourceId, data: ActivityCreate, user: Participant, db: Database
) -> RelationshipResponse:
    record = get_relationship(db, relationship_id, user, lock=True)
    require_open(record)
    db.add(Activity(relationship=record, author=user, **data.model_dump()))
    notify(
        db,
        other_participant(record.request, user.user_id),
        NotificationType.ACTIVITY_LOGGED,
        f"{user.name} logged an activity.",
        record,
    )
    db.flush()
    response = relationship_response(record)
    db.commit()
    return response


@engagement_router.post(
    "/relationships/{relationship_id}/feedback",
    responses={404: {"model": ErrorResponse, "description": "Relationship not found"}},
)
def save_feedback(
    relationship_id: ResourceId, data: FeedbackWrite, user: Participant, db: Database
) -> RelationshipResponse:
    record = get_relationship(db, relationship_id, user, lock=True)
    feedback = next(
        (item for item in record.feedback if item.given_by == user.user_id), None
    )
    if feedback is None:
        db.add(Feedback(relationship=record, author=user, **data.model_dump()))
        notify(
            db,
            other_participant(record.request, user.user_id),
            NotificationType.FEEDBACK_RECEIVED,
            f"{user.name} shared feedback.",
            record,
        )
    else:
        feedback.rating = data.rating
        feedback.comments = data.comments
    db.flush()
    response = relationship_response(record)
    db.commit()
    return response


@engagement_router.get("/feedback")
def list_feedback(user: Participant, db: Database) -> FeedbackList:
    author_filter = Feedback.given_by == user.user_id
    if user.role == UserRole.MENTOR:
        author_filter = Feedback.given_by == MentoringRequest.student_id
    rows = db.execute(
        select(Feedback, GuidanceArea.name)
        .join(Feedback.relationship)
        .join(MentoringRelationship.request)
        .join(MentoringRequest.area)
        .options(joinedload(Feedback.author))
        .where(request_owner(user), author_filter)
        .order_by(Feedback.created_at.desc(), Feedback.feedback_id.desc())
    )
    items = [
        FeedbackListItem(
            **FeedbackResponse.model_validate(item).model_dump(), area=area
        )
        for item, area in rows
    ]
    return FeedbackList(
        items=items,
        average=round(sum(item.rating for item in items) / len(items), 1)
        if items
        else None,
    )
