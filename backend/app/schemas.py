from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    EmailStr,
    Field,
    SecretStr,
    StringConstraints,
    model_validator,
)

from app.models import MentorVerification, UserRole


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["reachable"]


class ErrorResponse(BaseModel):
    detail: str


EmailAddress = Annotated[EmailStr, AfterValidator(str.lower)]
DisplayName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=255)
]
RollNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, to_upper=True, min_length=4, max_length=50
    ),
]
CareerObjective = Literal[
    "PLACEMENT", "HIGHER_STUDIES", "ENTREPRENEURSHIP", "CAREER_CLARITY"
]


class LoginRequest(BaseModel):
    email: EmailAddress
    password: SecretStr = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    role: UserRole
    name: DisplayName
    email: EmailAddress
    password: SecretStr = Field(min_length=8, max_length=128)
    roll_number: RollNumber | None = None
    career_objective: CareerObjective | None = None
    mentor_type: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None
    ) = None

    @model_validator(mode="after")
    def validate_student_roll_number(self) -> Self:
        if self.role == UserRole.STUDENT and self.roll_number is None:
            raise ValueError("A student roll number is required")
        return self


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    staff_type: str | None
    verification_status: MentorVerification | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserResponse
