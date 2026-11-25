from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.schemas.inventory import InventoryCreate, InventoryResponse, InventoryUpdate
from app.services import inventory_service

router = APIRouter(prefix="/admin/inventory", tags=["inventory"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[InventoryResponse])
def list_inventory(
    product_id: int | None = None, search: str | None = None, db: Session = Depends(get_db)
) -> list[InventoryResponse]:
    return inventory_service.list_units(db, product_id, search)


@router.post("", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_unit(data: InventoryCreate, db: Session = Depends(get_db)) -> InventoryResponse:
    return inventory_service.create_unit(db, data)


@router.patch("/{unit_id}", response_model=InventoryResponse)
def update_inventory_unit(unit_id: int, data: InventoryUpdate, db: Session = Depends(get_db)) -> InventoryResponse:
    return inventory_service.update_unit(db, unit_id, data)
