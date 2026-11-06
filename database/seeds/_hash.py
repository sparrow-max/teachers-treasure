from __future__ import annotations

import bcrypt

MAX_BCRYPT_BYTES = 72


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if not raw:
        raise ValueError("password must not be empty")
    if len(raw) > MAX_BCRYPT_BYTES:
        raise ValueError(
            f"password exceeds bcrypt limit of {MAX_BCRYPT_BYTES} bytes"
        )
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("ascii")