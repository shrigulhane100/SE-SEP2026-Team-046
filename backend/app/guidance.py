from typing import Annotated, get_args

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import Database, require_roles
from app.models import (
    GuidanceArea,
    MentoringRequest,
    MentorProfile,
    MentorVerification,
    User,
    UserRole,
    mentor_guidance_areas,
)
from app.profile_schemas import (
    GuidanceAreaCreate,
    GuidanceAreaResponse,
    GuidanceAreaUpdate,
    ManagedGuidanceArea,
    ProfileMetadata,
)
from app.schemas import CareerObjective, ErrorResponse

guidance_router = APIRouter(tags=["Guidance areas"])
admin_guidance_router = APIRouter(
    prefix="/admin/guidance-areas",
    tags=["Guidance areas"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Administrator access required"},
    },
)
AreaPath = Annotated[int, Path(gt=0, le=2147483647)]


@guidance_router.get("/guidance-areas")
def list_active_areas(db: Database) -> list[GuidanceAreaResponse]:
    """List the guidance areas currently available for selection."""
    return list(
        db.scalars(
            select(GuidanceArea)
            .where(GuidanceArea.is_active)
            .order_by(GuidanceArea.name)
        )
    )


@guidance_router.get("/meta")
def profile_metadata(db: Database) -> ProfileMetadata:
    """Return the choices used in the profile forms."""
    available_industries = db.scalars(
        select(MentorProfile.industry)
        .join(User, User.user_id == MentorProfile.user_id)
        .where(
            User.is_active,
            MentorProfile.verification_status == MentorVerification.VERIFIED,
            MentorProfile.industry.is_not(None),
            MentorProfile.industry != "",
        )
        .distinct()
        .order_by(MentorProfile.industry)
    )
    return ProfileMetadata(
        mentor_types=[
            "Recent Graduate",
            "Industry Professional",
            "Research Mentor",
            "Entrepreneur",
            "Faculty",
        ],
        career_objectives=list(get_args(CareerObjective)),
        industries=list(available_industries),
    )


@admin_guidance_router.get("")
def list_managed_areas(db: Database) -> list[ManagedGuidanceArea]:
    """List active and inactive areas with mentor and request counts."""
    counts = (
        select(mentor_guidance_areas.c.area_id, func.count().label("mentors"))
        .group_by(mentor_guidance_areas.c.area_id)
        .subquery()
    )
    request_counts = (
        select(MentoringRequest.area_id, func.count().label("requests"))
        .group_by(MentoringRequest.area_id)
        .subquery()
    )
    rows = db.execute(
        select(
            GuidanceArea,
            func.coalesce(counts.c.mentors, 0),
            func.coalesce(request_counts.c.requests, 0),
        )
        .outerjoin(counts, counts.c.area_id == GuidanceArea.area_id)
        .outerjoin(request_counts, request_counts.c.area_id == GuidanceArea.area_id)
        .order_by(GuidanceArea.name)
    )
    return [
        ManagedGuidanceArea(
            area_id=area.area_id,
            name=area.name,
            category=area.category,
            is_active=area.is_active,
            mentors=mentors,
            requests=requests,
        )
        for area, mentors, requests in rows
    ]


def save_area(db: Session, area: GuidanceArea) -> GuidanceAreaResponse:
    try:
        db.flush()
        response = GuidanceAreaResponse.model_validate(area)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if error.orig.diag.constraint_name == "uq_guidance_areas_name_ci":
            raise HTTPException(
                status_code=409, detail="Guidance area already exists"
            ) from None
        raise
    return response


@admin_guidance_router.post(
    "",
    status_code=201,
    responses={
        409: {"model": ErrorResponse, "description": "Area name already exists"}
    },
)
def create_area(data: GuidanceAreaCreate, db: Database) -> GuidanceAreaResponse:
    area = GuidanceArea(name=data.name, category=data.category)
    db.add(area)
    return save_area(db, area)


@admin_guidance_router.patch(
    "/{area_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Guidance area not found"},
        409: {"model": ErrorResponse, "description": "Area name already exists"},
    },
)
def update_area(
    area_id: AreaPath, data: GuidanceAreaUpdate, db: Database
) -> GuidanceAreaResponse:
    area = db.get(GuidanceArea, area_id, with_for_update=True)
    if area is None:
        raise HTTPException(status_code=404, detail="Guidance area not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(area, field, value)
    return save_area(db, area)
