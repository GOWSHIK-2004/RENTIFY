import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EquipmentCondition(str, enum.Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    DAMAGED = "DAMAGED"


class OperationalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"


class InventoryUnit(Base):
    """One physical item (for example camera CAM-001) of a product."""

    __tablename__ = "inventory_units"
    __table_args__ = (
        # Lets bookings reference (unit, product) together so a booking can
        # never point at a unit that belongs to a different product.
        UniqueConstraint("id", "product_id", name="uq_inventory_units_id_product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    asset_code: Mapped[str] = mapped_column(String(50), unique=True)
    condition: Mapped[EquipmentCondition] = mapped_column(
        Enum(EquipmentCondition, native_enum=False, length=20, create_constraint=True, name="equipment_condition"),
        default=EquipmentCondition.EXCELLENT,
    )
    operational_status: Mapped[OperationalStatus] = mapped_column(
        Enum(OperationalStatus, native_enum=False, length=20, create_constraint=True, name="operational_status"),
        default=OperationalStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="inventory_units")
    bookings = relationship("Booking", back_populates="inventory_unit", overlaps="product,bookings")
