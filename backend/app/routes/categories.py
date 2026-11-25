from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import allow_inactive, require_admin
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    include_inactive: bool = Depends(allow_inactive), db: Session = Depends(get_db)
) -> list[Category]:
    return category_service.list_categories(db, include_inactive)


@router.post(
    "", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)]
)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)) -> Category:
    return category_service.create_category(db, data)


@router.patch("/{category_id}", response_model=CategoryResponse, dependencies=[Depends(require_admin)])
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)) -> Category:
    return category_service.update_category(db, category_id, data)


@router.delete("/{category_id}", response_model=CategoryResponse, dependencies=[Depends(require_admin)])
def archive_category(category_id: int, db: Session = Depends(get_db)) -> Category:
    """Archives the category (it is never physically deleted)."""
    return category_service.archive_category(db, category_id)
