import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    PICKED_UP = "PICKED_UP"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("return_date > pickup_date", name="ck_bookings_return_after_pickup"),
        CheckConstraint("rental_days > 0", name="ck_bookings_rental_days_positive"),
        CheckConstraint("daily_price >= 0 AND total_amount >= 0", name="ck_bookings_amounts_non_negative"),
        # The unit must belong to the same product as the booking.
        ForeignKeyConstraint(
            ["inventory_unit_id", "product_id"],
            ["inventory_units.id", "inventory_units.product_id"],
            name="fk_bookings_unit_matches_product",
        ),
        # Same customer + same key = same checkout attempt (idempotency).
        UniqueConstraint("user_id", "idempotency_key", name="uq_bookings_user_idempotency_key"),
        # Speeds up the availability overlap query.
        Index("ix_bookings_unit_status_dates", "inventory_unit_id", "status", "pickup_date", "return_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_reference: Mapped[str] = mapped_column(String(20), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    inventory_unit_id: Mapped[int] = mapped_column(index=True)
    pickup_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date] = mapped_column(Date)
    rental_days: Mapped[int] = mapped_column(Integer)
    daily_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, native_enum=False, length=20, create_constraint=True, name="booking_status"),
        default=BookingStatus.CONFIRMED,
        index=True,
    )
    actual_pickup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_return_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookings")
    product = relationship("Product", back_populates="bookings", overlaps="bookings,inventory_unit")
    inventory_unit = relationship("InventoryUnit", back_populates="bookings", overlaps="bookings,product")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    review = relationship("Review", back_populates="booking", uselist=False)
