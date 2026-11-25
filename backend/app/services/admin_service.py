import math
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models.booking import Booking, BookingStatus
from app.models.inventory import InventoryUnit
from app.models.payment import Payment, PaymentStatus
from app.models.product import Product
from app.models.user import User, UserRole
from app.schemas.admin import (
    CustomerListResponse,
    CustomerSummary,
    DashboardResponse,
    MonthlyRevenue,
    PaymentListResponse,
    PaymentSummary,
    StatusCount,
    TopProduct,
)
from app.utils.dates import business_today
from app.utils.text import escape_like

REVENUE_MONTHS = 12


def _count(db: Session, model, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0


def _last_months(today: date, count: int) -> list[str]:
    """['2026-01', ..., '2026-11'] ending with the current month."""
    year, month = today.year, today.month
    months = []
    for _ in range(count):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return months[::-1]


def _monthly_revenue(db: Session, today: date) -> list[MonthlyRevenue]:
    # Revenue = successful (not refunded) simulated payments, grouped by month in the business timezone.
    month_label = func.to_char(func.timezone(get_settings().business_timezone, Payment.created_at), "YYYY-MM")
    rows = db.execute(
        select(month_label, func.sum(Payment.amount))
        .where(Payment.status == PaymentStatus.SUCCESS)
        .group_by(month_label)
    ).all()
    totals = {month: amount for month, amount in rows}
    return [MonthlyRevenue(month=m, revenue=totals.get(m, Decimal("0.00"))) for m in _last_months(today, REVENUE_MONTHS)]


def build_dashboard(db: Session) -> DashboardResponse:
    today = business_today()
    by_status = dict(db.execute(select(Booking.status, func.count()).group_by(Booking.status)).all())
    top_products = db.execute(
        select(Product.id, Product.name, func.count(Booking.id).label("bookings"))
        .join(Booking, Booking.product_id == Product.id)
        .where(Booking.status != BookingStatus.CANCELLED)
        .group_by(Product.id, Product.name)
        .order_by(func.count(Booking.id).desc(), Product.name)
        .limit(5)
    ).all()
    total_revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == PaymentStatus.SUCCESS)
    )
    return DashboardResponse(
        active_products=_count(db, Product, Product.is_active.is_(True)),
        inventory_units=_count(db, InventoryUnit),
        confirmed_bookings=by_status.get(BookingStatus.CONFIRMED, 0),
        active_rentals=by_status.get(BookingStatus.PICKED_UP, 0),
        completed_bookings=by_status.get(BookingStatus.RETURNED, 0),
        overdue_rentals=_count(db, Booking, Booking.status == BookingStatus.PICKED_UP, Booking.return_date < today),
        total_revenue=Decimal(total_revenue).quantize(Decimal("0.01")),
        monthly_revenue=_monthly_revenue(db, today),
        status_distribution=[StatusCount(status=s, count=by_status.get(s, 0)) for s in BookingStatus],
        top_products=[TopProduct(product_id=pid, name=name, bookings=n) for pid, name, n in top_products],
    )


def list_customers(db: Session, search: str | None, page: int, page_size: int) -> CustomerListResponse:
    conditions = [User.role == UserRole.CUSTOMER]
    if search:
        pattern = f"%{escape_like(search.strip())}%"
        conditions.append(or_(User.full_name.ilike(pattern, escape="\\"), User.email.ilike(pattern, escape="\\")))

    booking_counts = (
        select(Booking.user_id, func.count(Booking.id).label("booking_count")).group_by(Booking.user_id).subquery()
    )
    rows = db.execute(
        select(User, func.coalesce(booking_counts.c.booking_count, 0))
        .outerjoin(booking_counts, booking_counts.c.user_id == User.id)
        .where(*conditions)
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    total = _count(db, User, *conditions)
    return CustomerListResponse(
        items=[
            CustomerSummary(
                id=user.id, full_name=user.full_name, email=user.email, created_at=user.created_at, booking_count=n
            )
            for user, n in rows
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )


def list_payments(db: Session, payment_status: PaymentStatus | None, page: int, page_size: int) -> PaymentListResponse:
    conditions = [Payment.status == payment_status] if payment_status else []
    payments = db.scalars(
        select(Payment)
        .options(joinedload(Payment.booking).joinedload(Booking.user), joinedload(Payment.booking).joinedload(Booking.product))
        .where(*conditions)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).unique()
    total = _count(db, Payment, *conditions)
    return PaymentListResponse(
        items=[
            PaymentSummary(
                id=p.id,
                transaction_reference=p.transaction_reference,
                booking_reference=p.booking.booking_reference,
                customer_name=p.booking.user.full_name,
                product_name=p.booking.product.name,
                amount=p.amount,
                status=p.status,
                created_at=p.created_at,
            )
            for p in payments
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )
