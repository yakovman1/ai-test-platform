from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import AUTH_COOKIE_NAME, decode_access_token
from app.db.session import get_db
from app.models.user import User


def get_current_user(
    auth_token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    if auth_token is None:
        raise _unauthorized()

    try:
        user_id = int(decode_access_token(auth_token))
    except (JWTError, ValueError):
        raise _unauthorized() from None

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()

    return user


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )
