from __future__ import annotations

from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = DATABASE_DIR / "teacher_treasure.db"
DEFAULT_DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"