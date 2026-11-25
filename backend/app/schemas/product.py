from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.category import CategorySummary

Text100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Price = Annotated[Decimal, Field(gt=0, max_digits=10, decimal_places=2)]


class ProductCreate(BaseModel):
    category_id: int
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)]
    brand: Text100
    model: Text100
    short_description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    description: str = Field(min_length=1)
    daily_price: Price
    specifications: dict[str, str] = Field(default_factory=dict)
    is_featured: bool = False
    is_active: bool = True


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)] | None = None
    brand: Text100 | None = None
    model: Text100 | None = None
    short_description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)] | None = None
    description: str | None = Field(default=None, min_length=1)
    daily_price: Price | None = None
    specifications: dict[str, str] | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    brand: str
    model: str
    short_description: str
    description: str
    daily_price: Decimal
    image_url: str | None
    specifications: dict[str, str]
    is_featured: bool
    is_active: bool
    category: CategorySummary
    average_rating: float | None
    review_count: int
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int
