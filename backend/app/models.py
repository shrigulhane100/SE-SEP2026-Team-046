from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    false,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(StrEnum):
    STUDENT = "STUDENT"
    MENTOR = "MENTOR"
    ADMIN = "ADMIN"


class MentorVerification(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    user_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(320))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="chk_users_role", native_enum=False, create_constraint=True)
    )
    staff_type: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(server_default=true())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    student_profile: Mapped[StudentProfile | None] = relationship()
    mentor_profile: Mapped[MentorProfile | None] = relationship()


student_guidance_areas = Table(
    "student_guidance_areas",
    Base.metadata,
    Column(
        "student_profile_id",
        ForeignKey("student_profiles.profile_id"),
        primary_key=True,
    ),
    Column("area_id", ForeignKey("guidance_areas.area_id"), primary_key=True),
)

mentor_guidance_areas = Table(
    "mentor_guidance_areas",
    Base.metadata,
    Column(
        "mentor_profile_id", ForeignKey("mentor_profiles.profile_id"), primary_key=True
    ),
    Column("area_id", ForeignKey("guidance_areas.area_id"), primary_key=True),
)


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_student_profiles_user"),
        UniqueConstraint("roll_number", name="uq_student_profiles_roll"),
    )

    profile_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    roll_number: Mapped[str] = mapped_column(String(50))
    level: Mapped[str | None] = mapped_column(String(100))
    education: Mapped[str | None] = mapped_column(Text)
    interests: Mapped[str | None] = mapped_column(Text)
    career_stage: Mapped[str | None] = mapped_column(String(100))
    career_objective: Mapped[str | None] = mapped_column(String(30))
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    goals_summary: Mapped[str | None] = mapped_column(Text)
    preferred_mode: Mapped[str | None] = mapped_column(String(100))
    guidance_areas: Mapped[list[GuidanceArea]] = relationship(
        secondary=student_guidance_areas
    )


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_mentor_profiles_user"),
        CheckConstraint("experience_years >= 0", name="chk_mentor_experience"),
        CheckConstraint("max_mentees >= 1", name="chk_mentor_capacity"),
    )

    profile_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    mentor_type: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    current_role: Mapped[str | None] = mapped_column(String(150))
    organisation: Mapped[str | None] = mapped_column(String(150))
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    past_roles: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    academic_background: Mapped[str | None] = mapped_column(Text)
    experience_years: Mapped[int] = mapped_column(server_default="0")
    bio: Mapped[str | None] = mapped_column(Text)
    max_mentees: Mapped[int] = mapped_column(server_default="3")
    is_accepting: Mapped[bool] = mapped_column(server_default=false())
    verification_status: Mapped[MentorVerification] = mapped_column(
        Enum(
            MentorVerification,
            name="chk_mentor_verification",
            native_enum=False,
            create_constraint=True,
        ),
        server_default=MentorVerification.PENDING.value,
    )
    guidance_areas: Mapped[list[GuidanceArea]] = relationship(
        secondary=mentor_guidance_areas
    )


class GuidanceArea(Base):
    __tablename__ = "guidance_areas"
    area_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(server_default=true())


Index("uq_guidance_areas_name_ci", func.lower(GuidanceArea.name), unique=True)


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    __table_args__ = (Index("ix_auth_sessions_user_expiry", "user_id", "expires_at"),)

    session_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RequestStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class RelationshipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class MentoringType(StrEnum):
    ONE_TIME = "ONE_TIME"
    LONG_TERM = "LONG_TERM"


class MentoringRequest(Base):
    __tablename__ = "mentoring_requests"
    __table_args__ = (
        Index("ix_requests_student", "student_id"),
        Index("ix_requests_mentor", "mentor_id"),
        Index("ix_requests_status", "status"),
        Index("ix_requests_expiry", "expires_at"),
        Index(
            "uq_pending_request_pair",
            "student_id",
            "mentor_id",
            unique=True,
            postgresql_where=text("status = 'PENDING'"),
        ),
    )

    request_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    mentor_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    area_id: Mapped[int] = mapped_column(ForeignKey("guidance_areas.area_id"))
    message: Mapped[str] = mapped_column(Text)
    objective: Mapped[str] = mapped_column(Text, server_default="")
    type: Mapped[MentoringType] = mapped_column(
        Enum(
            MentoringType,
            name="chk_request_type",
            native_enum=False,
            create_constraint=True,
        )
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            name="chk_mentoring_request_status",
            native_enum=False,
            create_constraint=True,
        ),
        server_default=RequestStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reject_reason: Mapped[str | None] = mapped_column(Text)
    student: Mapped[User] = relationship(foreign_keys=[student_id])
    mentor: Mapped[User] = relationship(foreign_keys=[mentor_id])
    area: Mapped[GuidanceArea] = relationship()
    mentoring_relationship: Mapped[MentoringRelationship | None] = relationship(
        back_populates="request"
    )


class MentoringRelationship(Base):
    __tablename__ = "mentoring_relationships"
    __table_args__ = (UniqueConstraint("request_id", name="uq_relationship_request"),)

    relationship_id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("mentoring_requests.request_id"))
    status: Mapped[RelationshipStatus] = mapped_column(
        Enum(
            RelationshipStatus,
            name="chk_relationship_status",
            native_enum=False,
            create_constraint=True,
        ),
        server_default=RelationshipStatus.ACTIVE.value,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    request: Mapped[MentoringRequest] = relationship(
        back_populates="mentoring_relationship"
    )
