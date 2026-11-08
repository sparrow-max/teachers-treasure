from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import LocalDateTime, ORMModel


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    code: str = Field(min_length=1, max_length=32)

    @field_validator("name", "code", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ClassOut(ORMModel):
    id: int
    name: str
    code: str
    active: bool
    created_at: LocalDateTime