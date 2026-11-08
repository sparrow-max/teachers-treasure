from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import LocalDateTime, ORMModel


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=64)

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class UserOut(ORMModel):
    id: int
    username: str
    role: Literal["teacher", "monitor", "student"]
    display_name: str
    student_id: int | None
    must_change_password: bool
    active: bool
    created_at: LocalDateTime
    last_login_at: LocalDateTime | None


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=1)