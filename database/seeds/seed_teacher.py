from __future__ import annotations

import argparse
import os
import secrets

from sqlalchemy import update

from database.models import SYSTEM_ROLE_TEACHER, User, utcnow
from database.repositories import user_repo
from database.seeds._hash import hash_password
from database.session import session_scope


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the initial teacher account.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the password if the teacher account already exists.",
    )
    args = parser.parse_args()

    username = os.getenv("SEED_TEACHER_USERNAME", "teacher")
    display_name = os.getenv("SEED_TEACHER_DISPLAY_NAME", "教师")
    password = os.getenv("SEED_TEACHER_PASSWORD")
    generated = False

    with session_scope() as db:
        existing = user_repo.get_user_by_username(db, username)
        if existing is not None and not args.reset:
            print(
                f"teacher account '{username}' already exists; "
                "use --reset to reset the password"
            )
            return

        if not password:
            password = secrets.token_urlsafe(9)
            generated = True

        assert password is not None
        try:
            password_hash = hash_password(password)
        except ValueError as exc:
            raise SystemExit(
                f"invalid SEED_TEACHER_PASSWORD: {exc}"
            ) from exc

        if existing is not None:
            db.execute(
                update(User)
                .where(User.id == existing.id)
                .values(
                    password_hash=password_hash,
                    must_change_password=True,
                    token_version=User.token_version + 1,
                    active=True,
                    updated_at=utcnow(),
                )
            )
            print(f"teacher account '{username}' password reset")
        else:
            user_repo.create_user(
                db,
                username=username,
                password_hash=password_hash,
                role=SYSTEM_ROLE_TEACHER,
                display_name=display_name,
                student_id=None,
                must_change_password=True,
            )
            print(f"teacher account '{username}' created")

    if generated:
        print(f"generated password (shown once): {password}")
    print("first login must change the password")


if __name__ == "__main__":
    main()