import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_access_token

# auto_error=False so a missing header gives our own 401 instead of FastAPI's 403.
bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, message, headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate the Bearer token and load the user it belongs to."""
    if credentials is None:
        raise _unauthorized("Not authenticated.")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise _unauthorized("Invalid or expired token.")

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("Invalid or expired token.")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    # The role is read from the database row, not trusted from the token.
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator access required.")
    return current_user


def ensure_owner(owner_id: int, current_user: User) -> None:
    """Guard for private resources. Answers 404 (not 403) so ids of other users' data are not revealed."""
    if owner_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resource not found.")
