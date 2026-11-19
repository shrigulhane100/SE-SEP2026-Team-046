from datetime import datetime
from typing import Annotated

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.engagement_schemas import ActivityResponse, FeedbackResponse, GoalResponse
from app.models import MentoringType, RelationshipStatus, RequestStatus

ResourceId = Annotated[int, Path(gt=0, le=2147483647)]
BodyId = Annotated[int, Field(strict=True, gt=0, le=2147483647)]
RequestText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class RequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mentor_id: BodyId
    area_id: BodyId
    message: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=20, max_length=2000)
    ]
    objective: RequestText = ""
    type: MentoringType


class RequestRejection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: RequestText | None = None


class RelationshipStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RelationshipStatus


class StudentBrief(BaseModel):
    id: int
    name: str
    roll_number: str | None
    education: str | None
    career_stage: str | None
    career_objective: str | None


class MentorBrief(BaseModel):
    id: int
    name: str
    current_role: str | None
    organisation: str | None


class RequestResponse(BaseModel):
    id: int
    student_id: int
    mentor_id: int
    area_id: int
    message: str
    objective: str
    type: MentoringType
    status: RequestStatus
    created_at: datetime
    expires_at: datetime
    responded_at: datetime | None
    reject_reason: str | None
    area: str
    student: StudentBrief
    mentor: MentorBrief
    relationship_id: int | None
    hours_left: int | None


class RelationshipResponse(BaseModel):
    id: int
    request_id: int
    status: RelationshipStatus
    type: MentoringType
    started_at: datetime
    ended_at: datetime | None
    area: str
    student: StudentBrief
    mentor: MentorBrief
    goals: list[GoalResponse] = Field(default_factory=list)
    activities: list[ActivityResponse] = Field(default_factory=list)
    feedback: list[FeedbackResponse] = Field(default_factory=list)
    progress: int = 0


class AcceptanceResponse(BaseModel):
    request: RequestResponse
    relationship: RelationshipResponse
