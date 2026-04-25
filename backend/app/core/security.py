from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

AUTH_COOKIE_NAME = "auth_token"
ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60 * 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    return jwt.encode(
        {"sub": subject, "exp": expires_at},
        get_settings().jwt_secret,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise JWTError("Token is missing a subject")
    return subject
