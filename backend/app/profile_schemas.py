from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StringConstraints,
    field_validator,
)

from app.models import MentorVerification
from app.schemas import CareerObjective, DisplayName, RollNumber, UserResponse

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
MediumText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=150)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
Tag = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
AreaId = Annotated[int, Field(strict=True, gt=0, le=2147483647)]
AreaName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)
]


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: DisplayName | None = None
    education: LongText | None = None
    skills: list[Tag] = Field(default_factory=list, max_length=30)
    area_ids: list[AreaId] = Field(default_factory=list, max_length=50)

    @field_validator("name")
    @classmethod
    def require_non_null_name(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Name cannot be null")
        return value

    @field_validator("area_ids")
    @classmethod
    def require_unique_area_ids(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("Guidance area IDs must be unique")
        return value


class StudentProfileUpdate(ProfileUpdate):
    roll_number: RollNumber | None = None
    academic_level: Literal["Foundation", "Diploma", "Degree"] | None = None
    career_stage: ShortText | None = None
    career_objective: CareerObjective | None = None
    interests: LongText | None = None
    goals_summary: LongText | None = None
    preferred_mode: Literal["Online", "Chat", "Calls"] | None = None

    @field_validator("roll_number")
    @classmethod
    def require_non_null_roll_number(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Roll number cannot be null")
        return value


class MentorProfileUpdate(ProfileUpdate):
    mentor_type: ShortText | None = None
    industry: ShortText | None = None
    current_role: MediumText | None = None
    organisation: MediumText | None = None
    past_roles: list[Tag] = Field(default_factory=list, max_length=30)
    experience_years: Annotated[int, Field(strict=True, ge=0, le=60)] = 0
    bio: LongText | None = None
    max_mentees: Annotated[int, Field(strict=True, ge=1, le=20)] = 3
    is_accepting: StrictBool = True


TextValue = Annotated[
    str, BeforeValidator(lambda value: "" if value is None else value)
]
ListValue = Annotated[
    list[str], BeforeValidator(lambda value: [] if value is None else value)
]


class ProfileData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(validation_alias="profile_id")
    user_id: int
    skills: ListValue


class StudentProfileData(ProfileData):
    roll_number: str
    academic_level: TextValue = Field(validation_alias="level")
    education: TextValue
    career_stage: TextValue
    career_objective: TextValue
    interests: TextValue
    goals_summary: TextValue
    preferred_mode: TextValue


class MentorProfileData(ProfileData):
    mentor_type: TextValue
    industry: TextValue
    current_role: TextValue
    organisation: TextValue
    past_roles: ListValue
    experience_years: int
    bio: TextValue
    education: TextValue = Field(validation_alias="academic_background")
    max_mentees: int
    is_accepting: bool
    verification_status: MentorVerification


class ProfileUserResponse(UserResponse):
    profile_completion: int


class ProfileResponse(BaseModel):
    user: ProfileUserResponse
    profile: StudentProfileData | MentorProfileData
    area_ids: list[int]


class GuidanceAreaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(validation_alias="area_id")
    name: str
    category: str | None
    is_active: bool


class ManagedGuidanceArea(GuidanceAreaResponse):
    mentors: int
    requests: int = 0


class GuidanceAreaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: AreaName
    category: ShortText | None = None


class GuidanceAreaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: AreaName | None = None
    category: ShortText | None = None
    is_active: StrictBool | None = None

    @field_validator("name", "is_active")
    @classmethod
    def require_non_null_values(cls, value: str | bool | None) -> str | bool:
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class ProfileMetadata(BaseModel):
    mentor_types: list[str]
    career_objectives: list[CareerObjective]
    industries: list[str]
