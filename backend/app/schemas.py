from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["reachable"]


class ErrorResponse(BaseModel):
    detail: str
