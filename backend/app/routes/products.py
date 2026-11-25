from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import allow_inactive, get_optional_user, is_admin, require_admin
from app.models.user import User
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from app.services import product_service
from app.services.product_service import ProductFilters

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    q: str | None = Query(None, max_length=100, description="Search by name or brand"),
    category: str | None = Query(None, description="Category slug"),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    sort: Literal["newest", "price_asc", "price_desc"] = "newest",
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    include_inactive: bool = Depends(allow_inactive),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    filters = ProductFilters(q, category, min_price, max_price, sort, page, page_size)
    return product_service.list_products(db, filters, include_inactive)


# Declared before /{product_id} so "featured" is not parsed as an id.
@router.get("/featured", response_model=list[ProductResponse])
def featured_products(db: Session = Depends(get_db)) -> list[ProductResponse]:
    return product_service.list_featured(db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)
) -> ProductResponse:
    return product_service.get_product_response(db, product_id, include_inactive=is_admin(user))


@router.post(
    "", response_model=ProductResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)]
)
def create_product(data: ProductCreate, db: Session = Depends(get_db)) -> ProductResponse:
    return product_service.create_product(db, data)


@router.patch("/{product_id}", response_model=ProductResponse, dependencies=[Depends(require_admin)])
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)) -> ProductResponse:
    return product_service.update_product(db, product_id, data)


@router.delete("/{product_id}", response_model=ProductResponse, dependencies=[Depends(require_admin)])
def archive_product(product_id: int, db: Session = Depends(get_db)) -> ProductResponse:
    """Archives the product (is_active=false); booking history is preserved."""
    return product_service.archive_product(db, product_id)
