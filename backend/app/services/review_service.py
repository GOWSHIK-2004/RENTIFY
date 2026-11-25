from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.dependencies import ensure_owner
from app.models.booking import Booking, BookingStatus
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services.product_service import get_product_or_404


def _public_name(full_name: str) -> str:
    parts = full_name.split()
    return parts[0] if len(parts) == 1 else f"{parts[0]} {parts[-1][0]}."


def to_response(review: Review) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        product_id=review.product_id,
        booking_id=review.booking_id,
        user_id=review.user_id,
        reviewer_name=_public_name(review.user.full_name),
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def _load(db: Session, review_id: int) -> Review:
    review = db.scalar(select(Review).options(joinedload(Review.user)).where(Review.id == review_id))
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found.")
    return review


def list_product_reviews(db: Session, product_id: int) -> list[ReviewResponse]:
    get_product_or_404(db, product_id)
    reviews = db.scalars(
        select(Review)
        .options(joinedload(Review.user))
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc(), Review.id.desc())
    )
    return [to_response(review) for review in reviews]


def create_review(db: Session, user: User, data: ReviewCreate) -> ReviewResponse:
    booking = db.get(Booking, data.booking_id)
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found.")
    ensure_owner(booking.user_id, user)  # you can only review your own rentals

    # Eligibility is enforced here, not in the UI: the rental must be completed.
    if booking.status != BookingStatus.RETURNED:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can only review equipment after it has been returned.")
    if db.scalar(select(Review.id).where(Review.booking_id == booking.id)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already reviewed this booking.")

    # The product comes from the booking, never from the request.
    review = Review(user_id=user.id, product_id=booking.product_id, booking_id=booking.id,
                    rating=data.rating, comment=data.comment)
    db.add(review)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "You have already reviewed this booking.")
    return to_response(_load(db, review.id))


def update_review(db: Session, user: User, review_id: int, data: ReviewUpdate) -> ReviewResponse:
    review = _load(db, review_id)
    ensure_owner(review.user_id, user)
    changes = data.model_dump(exclude_unset=True)
    if "rating" in changes and changes["rating"] is not None:
        review.rating = changes["rating"]
    if "comment" in changes:
        review.comment = changes["comment"]
    db.commit()
    return to_response(_load(db, review_id))


def delete_review(db: Session, user: User, review_id: int) -> None:
    review = _load(db, review_id)
    ensure_owner(review.user_id, user)
    db.delete(review)
    db.commit()
