from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import LocalDateTime, ORMModel


class StudentCreate(BaseModel):
    class_id: int = Field(gt=0)
    student_no: str = Field(
        min_length=6,
        max_length=32,
        pattern=r"^[A-Za-z0-9_-]+$",
    )
    name: str = Field(min_length=1, max_length=32)
    role: Literal["学生", "班长"] = "学生"
    initial_password: str | None = None
    create_account: bool = True

    @field_validator("student_no", "name", "role", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class StudentOut(ORMModel):
    id: int
    class_id: int
    student_no: str
    name: str
    role: Literal["学生", "班长", "教师"]
    active: bool
    created_at: LocalDateTime