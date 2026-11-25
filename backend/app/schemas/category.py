from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

CategoryName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)]


class CategoryCreate(BaseModel):
    name: CategoryName
    description: str | None = None
    # Optional: generated from the name when omitted.
    slug: Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)] | None = None


class CategoryUpdate(BaseModel):
    name: CategoryName | None = None
    description: str | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    is_active: bool


class CategorySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
