import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user import RegisterRequest
from app.utils.security import hash_password, verify_password

logger = logging.getLogger("rentify.auth")


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def register_customer(db: Session, data: RegisterRequest) -> User:
    """Create a CUSTOMER account. The role is never taken from the request."""
    if get_user_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Two simultaneous registrations can both pass the check above;
        # the UNIQUE constraint on users.email is the final guard.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    logger.info("Registered user id=%s", user.id)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    # One generic message for both "no such user" and "wrong password"
    # so the API does not reveal which emails are registered.
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    return user
