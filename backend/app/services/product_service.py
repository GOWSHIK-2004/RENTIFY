import math
from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, contains_eager

from app.models.category import Category
from app.models.product import Product
from app.models.review import Review
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from app.utils.text import escape_like

SORT_ORDERS = {
    "newest": (Product.created_at.desc(), Product.id.desc()),
    "price_asc": (Product.daily_price.asc(), Product.id.asc()),
    "price_desc": (Product.daily_price.desc(), Product.id.desc()),
}


@dataclass
class ProductFilters:
    q: str | None = None
    category_slug: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    sort: str = "newest"
    page: int = 1
    page_size: int = 12


def lock_product(db: Session, product_id: int) -> Product:
    """SELECT ... FOR UPDATE on the product row.

    Booking allocation and inventory changes both take this lock first, so they
    run one after another for the same product instead of racing each other.
    The lock is released when the surrounding transaction commits or rolls back.
    """
    product = db.scalar(select(Product).where(Product.id == product_id).with_for_update())
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    return product


def _rating_stats():
    return (
        select(
            Review.product_id.label("product_id"),
            func.avg(Review.rating).label("average_rating"),
            func.count(Review.id).label("review_count"),
        )
        .group_by(Review.product_id)
        .subquery()
    )


def _products_query(include_inactive: bool) -> Select:
    """Product + category + rating stats in a single query (no N+1)."""
    stats = _rating_stats()
    query = (
        select(Product, stats.c.average_rating, func.coalesce(stats.c.review_count, 0))
        .join(Product.category)
        .outerjoin(stats, stats.c.product_id == Product.id)
        .options(contains_eager(Product.category))
    )
    if not include_inactive:
        query = query.where(Product.is_active.is_(True), Category.is_active.is_(True))
    return query


def _to_response(product: Product, average_rating, review_count: int) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        name=product.name,
        brand=product.brand,
        model=product.model,
        short_description=product.short_description,
        description=product.description,
        daily_price=product.daily_price,
        image_url=f"/uploads/{product.image_path}" if product.image_path else None,
        specifications=product.specifications or {},
        is_featured=product.is_featured,
        is_active=product.is_active,
        category=product.category,
        average_rating=round(float(average_rating), 1) if average_rating is not None else None,
        review_count=review_count,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def list_products(db: Session, filters: ProductFilters, include_inactive: bool) -> ProductListResponse:
    conditions = []
    if filters.q:
        pattern = f"%{escape_like(filters.q.strip())}%"
        conditions.append(or_(Product.name.ilike(pattern, escape="\\"), Product.brand.ilike(pattern, escape="\\")))
    if filters.category_slug:
        conditions.append(Category.slug == filters.category_slug)
    if filters.min_price is not None:
        conditions.append(Product.daily_price >= filters.min_price)
    if filters.max_price is not None:
        conditions.append(Product.daily_price <= filters.max_price)

    query = _products_query(include_inactive).where(*conditions)
    count_query = select(func.count()).select_from(Product).join(Product.category).where(*conditions)
    if not include_inactive:
        count_query = count_query.where(Product.is_active.is_(True), Category.is_active.is_(True))

    total = db.scalar(count_query) or 0
    rows = db.execute(
        query.order_by(*SORT_ORDERS[filters.sort])
        .limit(filters.page_size)
        .offset((filters.page - 1) * filters.page_size)
    ).all()
    return ProductListResponse(
        items=[_to_response(*row) for row in rows],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=math.ceil(total / filters.page_size),
    )


def list_featured(db: Session, limit: int = 8) -> list[ProductResponse]:
    rows = db.execute(
        _products_query(include_inactive=False)
        .where(Product.is_featured.is_(True))
        .order_by(Product.created_at.desc(), Product.id.desc())
        .limit(limit)
    ).all()
    return [_to_response(*row) for row in rows]


def get_product_response(db: Session, product_id: int, include_inactive: bool) -> ProductResponse:
    row = db.execute(_products_query(include_inactive).where(Product.id == product_id)).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    return _to_response(*row)


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    return product


def _require_category(db: Session, category_id: int) -> None:
    if db.get(Category, category_id) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Category does not exist.")


def create_product(db: Session, data: ProductCreate) -> ProductResponse:
    _require_category(db, data.category_id)
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    return get_product_response(db, product.id, include_inactive=True)


def update_product(db: Session, product_id: int, data: ProductUpdate) -> ProductResponse:
    product = get_product_or_404(db, product_id)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("category_id") is not None:
        _require_category(db, changes["category_id"])
    # Existing bookings keep their own stored daily_price, so a price change
    # here only affects future bookings.
    for field, value in changes.items():
        if value is not None:
            setattr(product, field, value)
    db.commit()
    return get_product_response(db, product_id, include_inactive=True)


def archive_product(db: Session, product_id: int) -> ProductResponse:
    """Soft delete: bookings, payments and reviews keep pointing at the product."""
    product = get_product_or_404(db, product_id)
    product.is_active = False
    db.commit()
    return get_product_response(db, product_id, include_inactive=True)
