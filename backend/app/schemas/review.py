from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Comment = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: Comment | None = None


class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: Comment | None = None


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    booking_id: int
    user_id: int
    # First name and last initial only: reviews are public.
    reviewer_name: str
    rating: int
    comment: str | None
    created_at: datetime
    updated_at: datetime
