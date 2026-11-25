from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status

from app.utils.dates import business_today

MIN_RENTAL_DAYS = 1
MAX_RENTAL_DAYS = 30
CENT = Decimal("0.01")


def rental_days(pickup_date: date, return_date: date) -> int:
    """The return date is not charged: Dec 1 -> Dec 4 is 3 days."""
    return (return_date - pickup_date).days


def validate_rental_dates(pickup_date: date, return_date: date) -> int:
    """Check the booking date rules and return the number of rental days."""
    if pickup_date < business_today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Pickup date cannot be in the past.")
    if return_date <= pickup_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Return date must be after the pickup date.")
    days = rental_days(pickup_date, return_date)
    if not MIN_RENTAL_DAYS <= days <= MAX_RENTAL_DAYS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Rental duration must be between {MIN_RENTAL_DAYS} and {MAX_RENTAL_DAYS} days.",
        )
    return days


def calculate_total(daily_price: Decimal, days: int) -> Decimal:
    """total_amount = daily_rental_price * rental_days, using Decimal (never float) for money."""
    return (daily_price * days).quantize(CENT, rounding=ROUND_HALF_UP)
