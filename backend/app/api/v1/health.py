from typing import Any

from fastapi import APIRouter

from app.core.response import ok

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    return ok({"status": "ok", "version": "1.1.0"})