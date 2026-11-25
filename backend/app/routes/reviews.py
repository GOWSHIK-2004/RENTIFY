from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewResponse, ReviewUpdate
from app.services import review_service

router = APIRouter(tags=["reviews"])


@router.get("/products/{product_id}/reviews", response_model=list[ReviewResponse])
def list_product_reviews(product_id: int, db: Session = Depends(get_db)) -> list[ReviewResponse]:
    return review_service.list_product_reviews(db, product_id)


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> ReviewResponse:
    return review_service.create_review(db, current_user, data)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    return review_service.update_review(db, current_user, review_id, data)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    review_service.delete_review(db, current_user, review_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
