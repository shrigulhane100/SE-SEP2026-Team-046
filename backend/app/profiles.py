from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import Database, require_roles, user_response
from app.mentoring_capacity import occupied_mentees
from app.models import GuidanceArea, MentorProfile, StudentProfile, User, UserRole
from app.profile_schemas import (
    MentorProfileData,
    MentorProfileUpdate,
    ProfileResponse,
    ProfileUserResponse,
    StudentProfileData,
    StudentProfileUpdate,
)
from app.schemas import ErrorResponse

profile_router = APIRouter(prefix="/profile", tags=["Profiles"])
ProfileOwner = Annotated[
    User, Depends(require_roles(UserRole.STUDENT, UserRole.MENTOR))
]
Profile = StudentProfile | MentorProfile


def find_profile(db: Session, user: User) -> Profile | None:
    model = StudentProfile if user.role == UserRole.STUDENT else MentorProfile
    return db.scalar(
        select(model)
        .options(selectinload(model.guidance_areas))
        .where(model.user_id == user.user_id)
    )


def profile_response(user: User, profile: Profile) -> ProfileResponse:
    area_ids = sorted(area.area_id for area in profile.guidance_areas)
    if isinstance(profile, StudentProfile):
        data = StudentProfileData.model_validate(profile)
        verification_status = None
        completed_fields = (
            data.roll_number,
            data.academic_level,
            data.education,
            data.career_stage,
            data.skills,
            data.interests,
            data.goals_summary,
            data.preferred_mode,
            data.career_objective,
            area_ids,
        )
    else:
        data = MentorProfileData.model_validate(profile)
        verification_status = profile.verification_status
        completed_fields = (
            data.mentor_type,
            data.industry,
            data.current_role,
            data.organisation,
            data.experience_years,
            data.bio,
            data.skills,
            data.education,
            area_ids,
        )
    account = user_response(user, verification_status)
    completion = round(100 * sum(map(bool, completed_fields)) / len(completed_fields))
    return ProfileResponse(
        user=ProfileUserResponse(**account.model_dump(), profile_completion=completion),
        profile=data,
        area_ids=area_ids,
    )


def selected_guidance_areas(
    db: Session, profile: Profile, area_ids: list[int]
) -> list[GuidanceArea]:
    existing_ids = {area.area_id for area in profile.guidance_areas}
    areas = list(
        db.scalars(
            select(GuidanceArea)
            .where(GuidanceArea.area_id.in_(area_ids))
            .order_by(GuidanceArea.area_id)
            .with_for_update(read=True)
        )
    )
    if len(areas) != len(area_ids):
        raise HTTPException(
            status_code=422, detail="One or more guidance areas do not exist"
        )
    if any(not area.is_active and area.area_id not in existing_ids for area in areas):
        raise HTTPException(
            status_code=422, detail="Inactive guidance areas cannot be selected"
        )
    return areas


@profile_router.get(
    "/me",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {
            "model": ErrorResponse,
            "description": "Student or mentor account required",
        },
        404: {"model": ErrorResponse, "description": "Profile not found"},
    },
)
def read_profile(user: ProfileOwner, db: Database) -> ProfileResponse:
    """Get the authenticated student or mentor's own profile."""
    profile = find_profile(db, user)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile_response(user, profile)


@profile_router.put(
    "/me",
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {
            "model": ErrorResponse,
            "description": "Student or mentor account required",
        },
        404: {"model": ErrorResponse, "description": "Account not found"},
        409: {"model": ErrorResponse, "description": "Roll number already registered"},
    },
)
def save_profile(
    data: StudentProfileUpdate | MentorProfileUpdate, user: ProfileOwner, db: Database
) -> ProfileResponse:
    """Create or update the caller's own profile and guidance-area selections."""
    student = user.role == UserRole.STUDENT
    allowed_fields = (
        StudentProfileUpdate.model_fields
        if student
        else MentorProfileUpdate.model_fields
    )
    if data.model_fields_set.difference(allowed_fields):
        raise HTTPException(
            status_code=422, detail="Profile fields do not match your account role"
        )

    # Serialize changes to the same account and its area mappings.
    account = db.scalar(
        select(User)
        .where(User.user_id == user.user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    profile = find_profile(db, account)
    details = data.model_dump(exclude_unset=True)
    if not student and "max_mentees" in details:
        occupied = db.scalar(occupied_mentees(account.user_id))
        if details["max_mentees"] < occupied:
            raise HTTPException(
                status_code=422,
                detail="Maximum mentees cannot be below current occupancy",
            )
    if profile is None:
        if student and "roll_number" not in details:
            raise HTTPException(
                status_code=422, detail="A student roll number is required"
            )
        profile = (
            StudentProfile(user_id=account.user_id)
            if student
            else MentorProfile(user_id=account.user_id)
        )
        db.add(profile)

    # Query and lock the target areas before mutating fields or flushing the profile.
    area_ids = details.pop("area_ids", None)
    if area_ids is not None:
        with db.no_autoflush:
            profile.guidance_areas = selected_guidance_areas(db, profile, area_ids)
    if "name" in details:
        account.name = details.pop("name")
    if "academic_level" in details:
        details["level"] = details.pop("academic_level")
    if not student and "education" in details:
        details["academic_background"] = details.pop("education")
    for field, value in details.items():
        setattr(profile, field, value)

    try:
        db.flush()
        response = profile_response(account, profile)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        if error.orig.diag.constraint_name == "uq_student_profiles_roll":
            raise HTTPException(
                status_code=409, detail="This roll number is already registered"
            ) from None
        raise
    return response
