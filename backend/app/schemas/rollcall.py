from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel


class RollcallCreate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=64)
    order_by: Literal["student_no", "name", "id"] = "student_no"

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class RecordOut(ORMModel):
    id: int
    session_id: int
    student_id: int
    student_no: str
    student_name: str
    role: Literal["学生", "班长", "教师"]
    order_no: int
    status: Literal["pending", "present", "absent"]
    checked_at: datetime | None


class SessionOut(ORMModel):
    id: int
    title: str
    status: Literal["calling", "ended"]
    order_by: Literal["student_no", "name", "id"]
    started_at: datetime
    ended_at: datetime | None
    total_count: int
    present_count: int
    absent_count: int
    pending_count: int


class SessionDetail(BaseModel):
    session: SessionOut
    records: list[RecordOut]