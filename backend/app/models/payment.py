import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    REFUNDED = "REFUNDED"


class Payment(Base):
    """Simulated payment record. No real money is ever moved."""

    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount >= 0", name="ck_payments_amount_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), unique=True)
    transaction_reference: Mapped[str] = mapped_column(String(40), unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=20, create_constraint=True, name="payment_status"),
        default=PaymentStatus.SUCCESS,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking = relationship("Booking", back_populates="payment")
