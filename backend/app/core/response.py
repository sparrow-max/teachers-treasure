from typing import Any

from fastapi.responses import JSONResponse


def ok(
    data: Any = None,
    message: str = "success",
) -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data}


def fail(
    code: int,
    message: str,
    http_status: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"code": int(code), "message": message, "data": None},
    )