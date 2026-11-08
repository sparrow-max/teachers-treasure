import argparse
import secrets
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories import user_repo
from app.services.auth_service import seed_teacher


def _generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or reset the teacher account",
    )
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    password = settings.seed_teacher_password
    generated = password is None
    if password is None:
        password = _generate_password()

    with SessionLocal() as db:
        existed = (
            user_repo.get_user_by_username(
                db,
                settings.seed_teacher_username,
            )
            is not None
        )
        user = seed_teacher(
            db,
            settings.seed_teacher_username,
            password,
            reset=args.reset,
        )

    print(f"teacher username: {user.username}")
    if generated and (not existed or args.reset):
        print(f"teacher password: {password}")
    elif existed and not args.reset:
        print("teacher account exists; use --reset to reset the password")


if __name__ == "__main__":
    main()