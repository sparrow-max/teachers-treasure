import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.core.errors import ApiError, ErrorCode
from app.core.logging import RequestContextMiddleware, configure_logging
from app.core.response import fail

logger = logging.getLogger("app.error")


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "参数校验失败"
    first = errors[0]
    location = [
        str(item)
        for item in first.get("loc", [])
        if item not in ("body", "query", "path")
    ]
    message = str(first.get("msg", "参数校验失败"))
    if location:
        return f"{'.'.join(location)}: {message}"
    return message


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    if settings.app_env == "production" and not os.getenv("JWT_SECRET"):
        raise RuntimeError("JWT_SECRET must be set in production")

    application = FastAPI(
        title="Teacher's-treasure API",
        version="1.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    application.include_router(api_router)

    @application.exception_handler(ApiError)
    async def api_error_handler(
        request: Request,
        exc: ApiError,
    ):
        logger.warning(
            "api_error code=%s path=%s request_id=%s",
            exc.code,
            request.url.path,
            getattr(request.state, "request_id", ""),
        )
        return fail(exc.code, exc.message, exc.http_status)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        logger.warning(
            "validation_error path=%s request_id=%s",
            request.url.path,
            getattr(request.state, "request_id", ""),
        )
        return fail(
            ErrorCode.VALIDATION_ERROR,
            _validation_message(exc),
            400,
        )

    @application.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ):
        logger.error(
            "unhandled_exception path=%s request_id=%s",
            request.url.path,
            getattr(request.state, "request_id", ""),
            exc_info=exc,
        )
        return fail(
            ErrorCode.INTERNAL_ERROR,
            "服务器内部错误",
            500,
        )

    return application


app = create_app()