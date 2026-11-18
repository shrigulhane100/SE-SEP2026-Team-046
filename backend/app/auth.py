from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_session
from app.models import (
    AuthSession,
    MentorProfile,
    MentorVerification,
    StudentProfile,
    User,
    UserRole,
)
from app.schemas import (
    ErrorResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    decode_access_token,
    hash_password,
    issue_access_token,
    verify_password,
)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])
bearer = HTTPBearer(auto_error=False)
Database = Annotated[Session, Depends(get_session)]


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


AuthSettings = Annotated[Settings, Depends(get_settings)]


def unauthorized(detail: str = "Invalid or expired access token") -> HTTPException:
    return HTTPException(
        status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def get_active_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Database,
    settings: AuthSettings,
) -> tuple[AuthSession, User]:
    if credentials is None:
        raise unauthorized("Authentication required")

    try:
        subject, session_id = decode_access_token(credentials.credentials, settings)
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized() from None

    row = db.execute(
        select(AuthSession, User)
        .join(User, User.user_id == AuthSession.user_id)
        .where(
            AuthSession.session_id == session_id,
            AuthSession.expires_at > datetime.now(UTC),
        )
    ).one_or_none()
    if row is None or str(row.User.user_id) != subject:
        raise unauthorized()
    if not row.User.is_active:
        raise HTTPException(status_code=403, detail="Your account has been deactivated")
    return row.AuthSession, row.User


ActiveSession = Annotated[tuple[AuthSession, User], Depends(get_active_session)]


def get_current_user(active_session: ActiveSession) -> User:
    return active_session[1]


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    def check_role(user: CurrentUser) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403, detail="You do not have permission for this action"
            )
        return user

    return check_role


def user_response(
    user: User, verification_status: MentorVerification | None
) -> UserResponse:
    return UserResponse(
        id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        staff_type=user.staff_type,
        verification_status=verification_status,
    )


def get_user_response(user: User, db: Session) -> UserResponse:
    verification_status = None
    if user.role == UserRole.MENTOR:
        verification_status = db.scalar(
            select(MentorProfile.verification_status).where(
                MentorProfile.user_id == user.user_id
            )
        )
    return user_response(user, verification_status)


@auth_router.post(
    "/register",
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Administrative accounts cannot self-register",
        },
        409: {
            "model": ErrorResponse,
            "description": "Email or roll number already registered",
        },
    },
)
def register(
    data: RegisterRequest, db: Database, settings: AuthSettings
) -> TokenResponse:
    """Create a student or mentor account and sign in."""
    if data.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=403, detail="Only student and mentor accounts can self-register"
        )

    if (
        db.scalar(select(User.user_id).where(func.lower(User.email) == data.email))
        is not None
    ):
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password.get_secret_value()),
        role=data.role,
    )
    db.add(user)
    try:
        db.flush()
        if data.role == UserRole.STUDENT:
            db.add(
                StudentProfile(
                    user_id=user.user_id,
                    roll_number=data.roll_number,
                    career_objective=data.career_objective,
                )
            )
        else:
            db.add(
                MentorProfile(
                    user_id=user.user_id,
                    mentor_type=data.mentor_type,
                    is_accepting=True,
                )
            )
        access_token = issue_access_token(db, user, settings)
        account = get_user_response(user, db)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        constraint = error.orig.diag.constraint_name
        if constraint == "uq_users_email":
            raise HTTPException(
                status_code=409, detail="An account with this email already exists"
            ) from None
        if constraint == "uq_student_profiles_roll":
            raise HTTPException(
                status_code=409, detail="This roll number is already registered"
            ) from None
        raise
    return TokenResponse(access_token=access_token, user=account)


@auth_router.post(
    "/login",
    responses={
        401: {"model": ErrorResponse, "description": "Incorrect email or password"},
        403: {"model": ErrorResponse, "description": "Account deactivated"},
    },
)
def login(data: LoginRequest, db: Database, settings: AuthSettings) -> TokenResponse:
    """Sign in with a JSON email and password."""
    user = db.scalar(select(User).where(func.lower(User.email) == data.email))
    stored_hash = user.password_hash if user else None
    if (
        not verify_password(data.password.get_secret_value(), stored_hash)
        or user is None
    ):
        raise unauthorized("Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Your account has been deactivated")
    token = issue_access_token(db, user, settings)
    account = get_user_response(user, db)
    db.commit()
    return TokenResponse(access_token=token, user=account)


@auth_router.get(
    "/me",
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Missing, expired or revoked token",
        },
        403: {"model": ErrorResponse, "description": "Account deactivated"},
    },
)
def me(user: CurrentUser, db: Database) -> UserResponse:
    return get_user_response(user, db)


@auth_router.post(
    "/logout",
    status_code=204,
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Missing, expired or revoked token",
        },
        403: {"model": ErrorResponse, "description": "Account deactivated"},
    },
)
def logout(active_session: ActiveSession, db: Database) -> Response:
    """Revoke the session associated with this bearer token."""
    session, _ = active_session
    db.delete(session)
    db.commit()
    return Response(status_code=204)


@admin_router.get(
    "/users",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Missing, expired or revoked token",
        },
        403: {"model": ErrorResponse, "description": "Administrator access required"},
    },
)
def list_users(
    db: Database,
    role: UserRole | None = None,
    q: Annotated[str | None, Query(max_length=320)] = None,
) -> list[UserResponse]:
    """List accounts for the administrator's user-management screen."""
    query = select(User, MentorProfile.verification_status).outerjoin(
        MentorProfile, User.user_id == MentorProfile.user_id
    )
    if role is not None:
        query = query.where(User.role == role)
    if q:
        query = query.where(
            or_(
                User.name.icontains(q, autoescape=True),
                User.email.icontains(q, autoescape=True),
            )
        )
    return [
        user_response(user, verification_status)
        for user, verification_status in db.execute(query.order_by(User.user_id))
    ]
