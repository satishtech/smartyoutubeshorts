"""Shared FastAPI dependencies (current user, ownership checks)."""
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.database import get_db
from app.exceptions import UnauthorizedError
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from a Bearer access token.

    Raises UnauthorizedError (401) if the token is missing, invalid, expired,
    not an access token, or the user no longer exists / is inactive.
    """
    if not token:
        raise UnauthorizedError("Not authenticated")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    return user
