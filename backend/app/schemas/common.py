from datetime import datetime, timezone
from typing import Annotated, Generic, TypeVar
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, PlainSerializer

from app.core.config import settings

T = TypeVar("T")


def _to_local_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ZoneInfo(settings.app_timezone)).isoformat()


LocalDateTime = Annotated[
    datetime,
    PlainSerializer(_to_local_iso, return_type=str, when_used="json"),
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: T


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class DeletedResult(BaseModel):
    id: int
    deleted: bool


class ChangedResult(BaseModel):
    changed: bool