from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.utils.text import slugify


def list_categories(db: Session, include_inactive: bool) -> list[Category]:
    query = select(Category).order_by(Category.name)
    if not include_inactive:
        query = query.where(Category.is_active)
    return list(db.scalars(query))


def get_category_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found.")
    return category


def _save(db: Session, category: Category) -> Category:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "A category with this name or slug already exists.")
    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    category = Category(name=data.name, slug=data.slug or slugify(data.name), description=data.description)
    db.add(category)
    return _save(db, category)


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category_or_404(db, category_id)
    # The slug is kept stable on rename so existing links keep working.
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    return _save(db, category)


def archive_category(db: Session, category_id: int) -> Category:
    """Categories are never hard-deleted: products and bookings reference them."""
    category = get_category_or_404(db, category_id)
    category.is_active = False
    return _save(db, category)
