import os
from dataclasses import dataclass
from functools import lru_cache


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: list[str]
    app_env: str
    log_level: str
    app_timezone: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    seed_teacher_username: str
    seed_teacher_password: str | None
    default_page_size: int
    max_page_size: int


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./teacher_treasure.db"),
        cors_origins=_split_csv(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173",
            )
        ),
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        app_timezone=os.getenv("APP_TIMEZONE", "Asia/Shanghai"),
        jwt_secret=os.getenv(
            "JWT_SECRET",
            "dev-only-insecure-jwt-secret-change-before-production",
        ),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "480")),
        seed_teacher_username=os.getenv("SEED_TEACHER_USERNAME", "teacher"),
        seed_teacher_password=os.getenv("SEED_TEACHER_PASSWORD") or None,
        default_page_size=int(os.getenv("DEFAULT_PAGE_SIZE", "20")),
        max_page_size=int(os.getenv("MAX_PAGE_SIZE", "100")),
    )


settings = get_settings()