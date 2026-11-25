from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.inventory import EquipmentCondition, InventoryUnit, OperationalStatus
from app.schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate
from app.services.product_service import get_product_or_404, lock_product
from app.utils.dates import business_today
from app.utils.text import escape_like


def to_response(unit: InventoryUnit) -> InventoryResponse:
    return InventoryResponse(
        id=unit.id,
        product_id=unit.product_id,
        product_name=unit.product.name,
        asset_code=unit.asset_code,
        condition=unit.condition,
        operational_status=unit.operational_status,
        created_at=unit.created_at,
    )


def is_usable(condition: EquipmentCondition, operational_status: OperationalStatus) -> bool:
    """Only ACTIVE, non-damaged units may be assigned to new bookings."""
    return operational_status == OperationalStatus.ACTIVE and condition != EquipmentCondition.DAMAGED


def list_units(db: Session, product_id: int | None = None, search: str | None = None) -> list[InventoryResponse]:
    query = select(InventoryUnit).options(joinedload(InventoryUnit.product)).order_by(InventoryUnit.asset_code)
    if product_id is not None:
        query = query.where(InventoryUnit.product_id == product_id)
    if search:
        query = query.where(InventoryUnit.asset_code.ilike(f"%{escape_like(search.strip())}%", escape="\\"))
    return [to_response(unit) for unit in db.scalars(query)]


def create_unit(db: Session, data: InventoryCreate) -> InventoryResponse:
    get_product_or_404(db, data.product_id)
    lock_product(db, data.product_id)
    unit = InventoryUnit(**data.model_dump())
    db.add(unit)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "This asset code is already in use.")
    return to_response(db.get(InventoryUnit, unit.id))


def unresolved_bookings(db: Session, unit_id: int) -> list[Booking]:
    """Bookings that still depend on this unit: equipment out, or confirmed and not yet finished."""
    return list(
        db.scalars(
            select(Booking).where(
                Booking.inventory_unit_id == unit_id,
                (Booking.status == BookingStatus.PICKED_UP)
                | ((Booking.status == BookingStatus.CONFIRMED) & (Booking.return_date > business_today())),
            )
        )
    )


def update_unit(db: Session, unit_id: int, data: InventoryUpdate) -> InventoryResponse:
    unit = db.get(InventoryUnit, unit_id)
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Inventory unit not found.")

    # Same product lock as booking allocation, so a unit cannot be taken
    # out of service while a booking is being assigned to it.
    lock_product(db, unit.product_id)
    db.refresh(unit)

    new_condition = data.condition or unit.condition
    new_status = data.operational_status or unit.operational_status
    if not is_usable(new_condition, new_status):
        blocking = unresolved_bookings(db, unit.id)
        if blocking:
            references = ", ".join(booking.booking_reference for booking in blocking)
            db.rollback()
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Resolve these bookings before taking this unit out of service: {references}.",
            )

    unit.condition = new_condition
    unit.operational_status = new_status
    db.commit()
    return to_response(db.get(InventoryUnit, unit_id))
