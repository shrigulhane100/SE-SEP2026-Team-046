from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints
from sqlalchemy import Select, and_, func, literal, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import Database, require_roles
from app.models import (
    GuidanceArea,
    MentorProfile,
    MentorVerification,
    StudentProfile,
    User,
    UserRole,
    mentor_guidance_areas,
    student_guidance_areas,
)
from app.profile_schemas import MentorProfileData
from app.schemas import ErrorResponse

mentor_router = APIRouter(tags=["Mentor discovery"])
student_mentor_router = APIRouter(
    prefix="/mentors",
    tags=["Mentor discovery"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Student account required"},
    },
)
verification_router = APIRouter(
    prefix="/admin",
    tags=["Mentor verification"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Administrator access required"},
    },
)
Student = Annotated[User, Depends(require_roles(UserRole.STUDENT))]
MentorId = Annotated[int, Path(gt=0, le=2147483647)]
FilterText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]


class MentorFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: FilterText | None = None
    area_id: int | None = Field(default=None, gt=0, le=2147483647)
    industry: FilterText | None = None
    mentor_type: FilterText | None = None
    availability: Literal["all", "available", "unavailable"] = "all"
    min_experience: int = Field(default=0, ge=0, le=60)
    sort: Literal["relevance", "experience"] = "relevance"
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0, le=2147483647)


class MentorResponse(BaseModel):
    id: int
    name: str
    mentor_type: str
    industry: str
    current_role: str
    organisation: str
    experience_years: int
    bio: str
    skills: list[str]
    past_roles: list[str]
    education: str
    area_ids: list[int]
    areas: list[str]
    max_mentees: int
    # Mentoring relationships and occupied capacity arrive with M3.5.
    active_mentees: int = 0
    is_accepting: bool
    verification_status: MentorVerification
    available: bool
    match: int | None = Field(ge=0, le=100)


class MentorVerificationResponse(MentorResponse):
    email: str
    registered_at: datetime


class VerificationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approve: StrictBool


class VerificationResult(BaseModel):
    ok: Literal[True] = True


def student_area_ids(db: Session, student_id: int) -> list[int]:
    return list(
        db.scalars(
            select(student_guidance_areas.c.area_id)
            .join(StudentProfile)
            .join(GuidanceArea)
            .where(StudentProfile.user_id == student_id, GuidanceArea.is_active)
        )
    )


def mentor_query(area_ids: list[int]) -> Select:
    if area_ids:
        matched = (
            select(func.count())
            .select_from(mentor_guidance_areas)
            .where(
                mentor_guidance_areas.c.mentor_profile_id == MentorProfile.profile_id,
                mentor_guidance_areas.c.area_id.in_(area_ids),
            )
            .correlate(MentorProfile)
            .scalar_subquery()
        )
    else:
        matched = literal(0)
    return (
        select(MentorProfile, User.name, matched.label("matched_areas"))
        .join(User, User.user_id == MentorProfile.user_id)
        .where(
            User.role == UserRole.MENTOR,
            User.is_active,
            MentorProfile.verification_status == MentorVerification.VERIFIED,
        )
        .options(
            selectinload(MentorProfile.guidance_areas.and_(GuidanceArea.is_active))
        )
    )


def apply_filters(query: Select, filters: MentorFilters) -> Select:
    if filters.q:
        query = query.where(
            or_(
                User.name.icontains(filters.q, autoescape=True),
                MentorProfile.current_role.icontains(filters.q, autoescape=True),
                MentorProfile.organisation.icontains(filters.q, autoescape=True),
                func.array_to_string(MentorProfile.skills, " ").icontains(
                    filters.q, autoescape=True
                ),
            )
        )
    if filters.area_id is not None:
        query = query.where(
            MentorProfile.guidance_areas.any(
                and_(GuidanceArea.area_id == filters.area_id, GuidanceArea.is_active)
            )
        )
    if filters.industry:
        query = query.where(
            func.lower(MentorProfile.industry) == filters.industry.lower()
        )
    if filters.mentor_type:
        query = query.where(
            func.lower(MentorProfile.mentor_type) == filters.mentor_type.lower()
        )
    if filters.availability != "all":
        query = query.where(
            MentorProfile.is_accepting.is_(filters.availability == "available")
        )
    if filters.min_experience:
        query = query.where(MentorProfile.experience_years >= filters.min_experience)

    if filters.sort == "relevance":
        query = query.order_by(
            MentorProfile.is_accepting.desc(),
            query.selected_columns.matched_areas.desc(),
        )
    return (
        query.order_by(MentorProfile.experience_years.desc(), User.user_id)
        .offset(filters.offset)
        .limit(filters.limit)
    )


def mentor_response(
    profile: MentorProfile,
    name: str,
    *,
    matches: int = 0,
    student_area_count: int = 0,
    account_active: bool = True,
) -> MentorResponse:
    fields = MentorProfileData.model_validate(profile).model_dump(
        exclude={"id", "user_id"}
    )
    areas = sorted(
        (area for area in profile.guidance_areas if area.is_active),
        key=lambda area: area.area_id,
    )
    # Round half up so the score matches the frontend prototype.
    match = (
        (100 * matches + student_area_count // 2) // student_area_count
        if student_area_count
        else None
    )
    return MentorResponse(
        **fields,
        id=profile.user_id,
        name=name,
        area_ids=[area.area_id for area in areas],
        areas=[area.name for area in areas],
        available=(
            account_active
            and profile.verification_status == MentorVerification.VERIFIED
            and profile.is_accepting
        ),
        match=match,
    )


def find_mentors(
    db: Session, filters: MentorFilters, preferences: list[int]
) -> list[MentorResponse]:
    rows = db.execute(apply_filters(mentor_query(preferences), filters))
    return [
        mentor_response(
            profile, name, matches=matches, student_area_count=len(preferences)
        )
        for profile, name, matches in rows
    ]


@mentor_router.get("/public/mentors")
def list_public_mentors(
    filters: Annotated[MentorFilters, Query()], db: Database
) -> list[MentorResponse]:
    """List public profiles for active, verified mentors."""
    return find_mentors(db, filters, [])


@student_mentor_router.get("")
def list_mentors(
    filters: Annotated[MentorFilters, Query()], student: Student, db: Database
) -> list[MentorResponse]:
    """Search, filter and rank mentors for the signed-in student."""
    return find_mentors(db, filters, student_area_ids(db, student.user_id))


@student_mentor_router.get(
    "/{mentor_id}",
    responses={404: {"model": ErrorResponse, "description": "Mentor not found"}},
)
def get_mentor(mentor_id: MentorId, student: Student, db: Database) -> MentorResponse:
    """Get a verified mentor and their match score for the signed-in student."""
    preferences = student_area_ids(db, student.user_id)
    row = db.execute(
        mentor_query(preferences).where(User.user_id == mentor_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Mentor not found")
    profile, name, matches = row
    return mentor_response(
        profile, name, matches=matches, student_area_count=len(preferences)
    )


@verification_router.get("/mentor-verifications")
def list_mentor_verifications(db: Database) -> list[MentorVerificationResponse]:
    """List mentor profiles for the administrator's verification screen."""
    rows = db.execute(
        select(MentorProfile, User.name, User.email, User.created_at, User.is_active)
        .join(User, User.user_id == MentorProfile.user_id)
        .where(User.role == UserRole.MENTOR)
        .options(
            selectinload(MentorProfile.guidance_areas.and_(GuidanceArea.is_active))
        )
        .order_by(
            (MentorProfile.verification_status == MentorVerification.PENDING).desc(),
            User.user_id,
        )
    )
    return [
        MentorVerificationResponse(
            **mentor_response(profile, name, account_active=is_active).model_dump(),
            email=email,
            registered_at=created_at,
        )
        for profile, name, email, created_at, is_active in rows
    ]


@verification_router.post(
    "/mentors/{mentor_id}/verify",
    responses={404: {"model": ErrorResponse, "description": "Mentor not found"}},
)
def verify_mentor(
    mentor_id: MentorId, decision: VerificationDecision, db: Database
) -> VerificationResult:
    """Approve a mentor or revoke their visibility in discovery."""
    profile = db.scalar(
        select(MentorProfile)
        .join(User, User.user_id == MentorProfile.user_id)
        .where(User.user_id == mentor_id, User.role == UserRole.MENTOR)
        .with_for_update(of=MentorProfile)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Mentor not found")
    profile.verification_status = (
        MentorVerification.VERIFIED if decision.approve else MentorVerification.REJECTED
    )
    db.commit()
    return VerificationResult()
