from datetime import UTC, date, datetime
from typing import Annotated, Literal

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from app.models import ActivityType, GoalStatus, NotificationReference, NotificationType

GoalTitle = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: GoalTitle
    target_date: date | None = None


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: GoalTitle | None = None
    status: GoalStatus | None = None
    target_date: date | None = None

    @field_validator("title", "status")
    @classmethod
    def require_values(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class ActivityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_type: ActivityType
    notes: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
    ]
    activity_date: date = Field(default_factory=lambda: datetime.now(UTC).date())

    @field_validator("activity_date")
    @classmethod
    def reject_future_dates(cls, value: date) -> date:
        if value > datetime.now(UTC).date():
            raise ValueError("Activity date cannot be in the future")
        return value


class FeedbackWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: Annotated[int, Field(strict=True, ge=1, le=5)]
    comments: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=2000)
    ] = ""


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(validation_alias="goal_id")
    relationship_id: int
    title: str
    status: GoalStatus
    target_date: date | None
    created_by: int
    created_by_name: str = Field(validation_alias=AliasPath("author", "name"))
    created_at: datetime


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(validation_alias="activity_id")
    relationship_id: int
    activity_type: ActivityType
    notes: str
    activity_date: date
    created_by: int
    created_by_name: str = Field(validation_alias=AliasPath("author", "name"))
    created_at: datetime


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, validate_by_name=True)

    id: int = Field(validation_alias="feedback_id")
    relationship_id: int
    given_by: int
    given_by_name: str = Field(validation_alias=AliasPath("author", "name"))
    rating: int
    comments: str
    created_at: datetime


class FeedbackListItem(FeedbackResponse):
    area: str


class FeedbackList(BaseModel):
    items: list[FeedbackListItem]
    average: float | None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(validation_alias="notification_id")
    user_id: int
    type: NotificationType
    message: str
    reference_type: NotificationReference
    reference_id: int
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    items: list[NotificationResponse]
    unread: int


class NotificationReadResult(BaseModel):
    ok: Literal[True] = True
