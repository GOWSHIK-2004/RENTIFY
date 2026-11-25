import hashlib
import logging
import math
import secrets
from datetime import UTC, date, datetime
from typing import NoReturn

from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.inventory import EquipmentCondition, InventoryUnit, OperationalStatus
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingCustomer,
    BookingListResponse,
    BookingProduct,
    BookingResponse,
    QuoteResponse,
)
from app.dependencies import ensure_owner
from app.services import pricing_service
from app.services.inventory_service import is_usable, unresolved_bookings
from app.services.product_service import lock_product
from app.utils.dates import business_today
from app.utils.text import escape_like

logger = logging.getLogger("rentify.bookings")

# Statuses that hold a physical unit for their date range.
ACTIVE_STATUSES = (BookingStatus.CONFIRMED, BookingStatus.PICKED_UP)

# Booking status transitions. Anything not listed here is rejected.
ALLOWED_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.CONFIRMED: {BookingStatus.PICKED_UP, BookingStatus.CANCELLED},
    BookingStatus.PICKED_UP: {BookingStatus.RETURNED},
    BookingStatus.RETURNED: set(),
    BookingStatus.CANCELLED: set(),
}

REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I to avoid misreading


# --------------------------------------------------------------------------
# Availability and quotes
# --------------------------------------------------------------------------
def _abort(db: Session, status_code: int, detail: str | dict) -> NoReturn:
    """Roll back (which also releases any row lock) and raise an HTTP error."""
    db.rollback()
    raise HTTPException(status_code, detail)


def get_bookable_product(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or not product.is_active or not product.category.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    return product


def _available_unit_conditions(product_id: int, pickup_date: date, return_date: date) -> list:
    """SQL conditions selecting the product's units that can take a booking for these dates."""
    # Two date ranges [a, b) and [c, d) overlap exactly when a < d AND b > c.
    # Dec 1-5 vs Dec 3-7 overlap; Dec 1-5 vs Dec 5-8 do not (return day is free).
    overlapping_booking_units = select(Booking.inventory_unit_id).where(
        Booking.status.in_(ACTIVE_STATUSES),
        Booking.pickup_date < return_date,
        Booking.return_date > pickup_date,
    )
    # A unit that is still out past its return date is not physically back,
    # so it is excluded from new allocations whatever the requested dates.
    overdue_unit_ids = select(Booking.inventory_unit_id).where(
        Booking.status == BookingStatus.PICKED_UP,
        Booking.return_date < business_today(),
    )
    return [
        InventoryUnit.product_id == product_id,
        InventoryUnit.operational_status == OperationalStatus.ACTIVE,
        InventoryUnit.condition != EquipmentCondition.DAMAGED,
        InventoryUnit.id.not_in(overlapping_booking_units),
        InventoryUnit.id.not_in(overdue_unit_ids),
    ]


def build_quote(db: Session, product_id: int, pickup_date: date, return_date: date) -> QuoteResponse:
    """Duration, price and availability for a product and dates (read-only, nothing reserved)."""
    days = pricing_service.validate_rental_dates(pickup_date, return_date)
    product = get_bookable_product(db, product_id)
    available_units = db.scalar(
        select(func.count()).select_from(InventoryUnit).where(
            *_available_unit_conditions(product.id, pickup_date, return_date)
        )
    )
    return QuoteResponse(
        product_id=product.id,
        pickup_date=pickup_date,
        return_date=return_date,
        rental_days=days,
        daily_price=product.daily_price,
        total_amount=pricing_service.calculate_total(product.daily_price, days),
        available=available_units > 0,
        available_units=available_units,
    )


# --------------------------------------------------------------------------
# Creating a booking (checkout)
# --------------------------------------------------------------------------
def _fingerprint(data: BookingCreate) -> str:
    """Identifies what a checkout request asks for, so a reused idempotency key can be checked."""
    raw = f"{data.product_id}|{data.pickup_date.isoformat()}|{data.return_date.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _new_reference(db: Session) -> str:
    while True:
        reference = "RNT-" + "".join(secrets.choice(REFERENCE_ALPHABET) for _ in range(8))
        if db.scalar(select(Booking.id).where(Booking.booking_reference == reference)) is None:
            return reference


def create_booking(db: Session, user: User, data: BookingCreate) -> tuple[Booking, bool]:
    """Simulated checkout. Returns (booking, created); created is False for an idempotent replay.

    Everything below runs in ONE database transaction:
      1. lock the product row (FOR UPDATE) so concurrent checkouts of this product queue up
      2. re-check availability *after* acquiring the lock
      3. insert the booking and its payment, then commit both together
    Any early exit rolls back, so a failed payment or conflict reserves nothing.
    """
    pricing_service.validate_rental_dates(data.pickup_date, data.return_date)
    days = pricing_service.rental_days(data.pickup_date, data.return_date)
    fingerprint = _fingerprint(data)

    product = lock_product(db, data.product_id)

    # Idempotency: the same key from the same customer must not create a second booking.
    # Checked after the lock so two simultaneous retries cannot both slip through.
    previous = db.scalar(
        select(Booking).where(Booking.user_id == user.id, Booking.idempotency_key == data.idempotency_key)
    )
    if previous is not None:
        if previous.request_fingerprint != fingerprint:
            _abort(db, status.HTTP_422_UNPROCESSABLE_ENTITY, "This idempotency key was already used for a different request.")
        db.rollback()
        return previous, False

    if not product.is_active or not product.category.is_active:
        _abort(db, status.HTTP_404_NOT_FOUND, "Product not found.")

    if data.payment_outcome == "failure":
        _abort(db, status.HTTP_402_PAYMENT_REQUIRED, "Simulated payment failed. No booking was created and no equipment was reserved.")

    unit = db.scalar(
        select(InventoryUnit)
        .where(*_available_unit_conditions(product.id, data.pickup_date, data.return_date))
        .order_by(InventoryUnit.asset_code)
        .limit(1)
    )
    if unit is None:
        _abort(db, status.HTTP_409_CONFLICT, "This equipment is no longer available for the selected dates.")

    # The server's price is the only price. The customer's expected_total just
    # tells us whether they agreed to the number we are about to charge.
    total = pricing_service.calculate_total(product.daily_price, days)
    if data.expected_total != total:
        _abort(
            db,
            status.HTTP_409_CONFLICT,
            {
                "code": "PRICE_CHANGED",
                "message": "The rental price has changed. Please review the updated total.",
                "daily_price": str(product.daily_price),
                "rental_days": days,
                "total_amount": str(total),
            },
        )

    booking = Booking(
        booking_reference=_new_reference(db),
        user_id=user.id,
        product_id=product.id,
        inventory_unit_id=unit.id,
        pickup_date=data.pickup_date,
        return_date=data.return_date,
        rental_days=days,
        daily_price=product.daily_price,  # snapshot: later price edits never change this booking
        total_amount=total,
        status=BookingStatus.CONFIRMED,
        idempotency_key=data.idempotency_key,
        request_fingerprint=fingerprint,
    )
    booking.payment = Payment(
        transaction_reference="TXN-" + secrets.token_hex(8).upper(),
        amount=total,
        status=PaymentStatus.SUCCESS,
    )
    db.add(booking)
    try:
        db.commit()  # booking + payment become visible together, and the product lock is released
    except IntegrityError:
        _abort(db, status.HTTP_409_CONFLICT, "The booking could not be completed. Please try again.")
    logger.info("Booking %s created (unit %s, user %s)", booking.booking_reference, unit.asset_code, user.id)
    return booking, True


# --------------------------------------------------------------------------
# Status changes
# --------------------------------------------------------------------------
def _lock_booking(db: Session, booking_id: int) -> Booking:
    """Lock the booking row so two requests cannot change its status at the same time."""
    booking = db.scalar(select(Booking).where(Booking.id == booking_id).with_for_update())
    if booking is None:
        _abort(db, status.HTTP_404_NOT_FOUND, "Booking not found.")
    return booking


def _check_transition(db: Session, booking: Booking, new_status: BookingStatus) -> None:
    if new_status not in ALLOWED_TRANSITIONS[booking.status]:
        _abort(
            db,
            status.HTTP_400_BAD_REQUEST,
            f"A booking that is {booking.status.value} cannot become {new_status.value}.",
        )


def cancel_booking(db: Session, booking_id: int, user: User, reason: str | None, as_admin: bool) -> Booking:
    booking = _lock_booking(db, booking_id)
    if not as_admin and booking.user_id != user.id:
        _abort(db, status.HTTP_404_NOT_FOUND, "Booking not found.")
    _check_transition(db, booking, BookingStatus.CANCELLED)
    # Customers may only cancel before the pickup date; administrators may cancel any confirmed booking.
    if not as_admin and business_today() >= booking.pickup_date:
        _abort(db, status.HTTP_400_BAD_REQUEST, "Bookings can only be cancelled before the pickup date.")

    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = reason or ("Cancelled by administrator" if as_admin else "Cancelled by customer")
    # Refund in the same transaction as the cancellation: both happen or neither does.
    if booking.payment is not None and booking.payment.status == PaymentStatus.SUCCESS:
        booking.payment.status = PaymentStatus.REFUNDED
    db.commit()
    logger.info("Booking %s cancelled", booking.booking_reference)
    return booking


def pickup_booking(db: Session, booking_id: int) -> Booking:
    booking = _lock_booking(db, booking_id)
    _check_transition(db, booking, BookingStatus.PICKED_UP)

    today = business_today()
    if not booking.pickup_date <= today < booking.return_date:
        _abort(
            db,
            status.HTTP_400_BAD_REQUEST,
            f"Pickup is only possible during the scheduled rental period "
            f"({booking.pickup_date} to {booking.return_date}).",
        )
    unit = db.get(InventoryUnit, booking.inventory_unit_id)
    if not is_usable(unit.condition, unit.operational_status):
        _abort(db, status.HTTP_409_CONFLICT, "This unit is not in service.")
    still_out = db.scalar(
        select(Booking.id).where(
            Booking.inventory_unit_id == booking.inventory_unit_id,
            Booking.status == BookingStatus.PICKED_UP,
            Booking.id != booking.id,
        )
    )
    if still_out is not None:
        _abort(db, status.HTTP_409_CONFLICT, "This unit has not been returned from a previous rental yet.")

    booking.status = BookingStatus.PICKED_UP
    booking.actual_pickup_at = datetime.now(UTC)
    db.commit()
    logger.info("Booking %s picked up", booking.booking_reference)
    return booking


def return_booking(db: Session, booking_id: int, condition: EquipmentCondition | None) -> Booking:
    booking = _lock_booking(db, booking_id)
    _check_transition(db, booking, BookingStatus.RETURNED)

    unit = db.get(InventoryUnit, booking.inventory_unit_id)
    if condition is not None and condition != unit.condition:
        # Same product lock as allocation, so no booking is assigned while the condition changes.
        lock_product(db, booking.product_id)
        if not is_usable(condition, unit.operational_status):
            blocking = unresolved_bookings(db, unit.id, exclude_booking_id=booking.id)
            if blocking:
                references = ", ".join(b.booking_reference for b in blocking)
                _abort(
                    db,
                    status.HTTP_409_CONFLICT,
                    f"Cancel or resolve these upcoming bookings before marking the unit {condition.value}: {references}.",
                )
        unit.condition = condition

    booking.status = BookingStatus.RETURNED
    booking.actual_return_at = datetime.now(UTC)
    db.commit()
    logger.info("Booking %s returned", booking.booking_reference)
    return booking


# --------------------------------------------------------------------------
# Reading bookings
# --------------------------------------------------------------------------
def _with_details(query: Select) -> Select:
    return query.options(
        joinedload(Booking.product),
        joinedload(Booking.inventory_unit),
        joinedload(Booking.payment),
        joinedload(Booking.user),
        joinedload(Booking.review),
    )


def _overdue_unit_ids(db: Session) -> set[int]:
    return set(
        db.scalars(
            select(Booking.inventory_unit_id).where(
                Booking.status == BookingStatus.PICKED_UP, Booking.return_date < business_today()
            )
        )
    )


def to_response(booking: Booking, overdue_unit_ids: set[int]) -> BookingResponse:
    today = business_today()
    is_overdue = booking.status == BookingStatus.PICKED_UP and booking.return_date < today
    # A confirmed booking is "affected" when its unit has not come back from an overdue rental.
    affected = (
        booking.status == BookingStatus.CONFIRMED
        and booking.inventory_unit_id in overdue_unit_ids
        and booking.return_date >= today
    )
    product = booking.product
    return BookingResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        status=booking.status,
        product=BookingProduct(
            id=product.id,
            name=product.name,
            brand=product.brand,
            model=product.model,
            image_url=f"/uploads/{product.image_path}" if product.image_path else None,
        ),
        customer=BookingCustomer(id=booking.user.id, full_name=booking.user.full_name, email=booking.user.email),
        asset_code=booking.inventory_unit.asset_code,
        pickup_date=booking.pickup_date,
        return_date=booking.return_date,
        rental_days=booking.rental_days,
        daily_price=booking.daily_price,
        total_amount=booking.total_amount,
        payment_status=booking.payment.status if booking.payment else None,
        transaction_reference=booking.payment.transaction_reference if booking.payment else None,
        actual_pickup_at=booking.actual_pickup_at,
        actual_return_at=booking.actual_return_at,
        cancellation_reason=booking.cancellation_reason,
        created_at=booking.created_at,
        is_overdue=is_overdue,
        affected_by_overdue=affected,
        can_cancel=booking.status == BookingStatus.CONFIRMED and today < booking.pickup_date,
        review_id=booking.review.id if booking.review else None,
    )


def get_booking_response(db: Session, booking_id: int, owner: User | None = None) -> BookingResponse:
    """Load one booking. With `owner`, only that customer's own booking is visible."""
    booking = db.scalar(_with_details(select(Booking).where(Booking.id == booking_id)))
    if booking is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found.")
    if owner is not None:
        ensure_owner(booking.user_id, owner)
    return to_response(booking, _overdue_unit_ids(db))


def list_customer_bookings(db: Session, user: User, booking_status: BookingStatus | None) -> list[BookingResponse]:
    query = _with_details(select(Booking).where(Booking.user_id == user.id))
    if booking_status is not None:
        query = query.where(Booking.status == booking_status)
    overdue_units = _overdue_unit_ids(db)
    bookings = db.scalars(query.order_by(Booking.created_at.desc(), Booking.id.desc())).unique()
    return [to_response(booking, overdue_units) for booking in bookings]


def list_admin_bookings(
    db: Session,
    booking_status: BookingStatus | None,
    overdue_only: bool,
    search: str | None,
    page: int,
    page_size: int,
) -> BookingListResponse:
    conditions = []
    if booking_status is not None:
        conditions.append(Booking.status == booking_status)
    if overdue_only:
        conditions += [Booking.status == BookingStatus.PICKED_UP, Booking.return_date < business_today()]
    if search:
        pattern = f"%{escape_like(search.strip())}%"
        conditions.append(
            or_(
                Booking.booking_reference.ilike(pattern, escape="\\"),
                Booking.user.has(User.full_name.ilike(pattern, escape="\\")),
                Booking.user.has(User.email.ilike(pattern, escape="\\")),
                Booking.product.has(Product.name.ilike(pattern, escape="\\")),
            )
        )

    total = db.scalar(select(func.count()).select_from(Booking).where(*conditions)) or 0
    bookings = db.scalars(
        _with_details(select(Booking).where(*conditions))
        .order_by(Booking.created_at.desc(), Booking.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).unique()
    overdue_units = _overdue_unit_ids(db)
    return BookingListResponse(
        items=[to_response(booking, overdue_units) for booking in bookings],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )
