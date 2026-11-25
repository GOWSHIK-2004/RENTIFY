from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.models.inventory import EquipmentCondition, OperationalStatus

AssetCode = Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=2, max_length=50)]


class InventoryCreate(BaseModel):
    product_id: int
    asset_code: AssetCode
    condition: EquipmentCondition = EquipmentCondition.EXCELLENT
    operational_status: OperationalStatus = OperationalStatus.ACTIVE


class InventoryUpdate(BaseModel):
    condition: EquipmentCondition | None = None
    operational_status: OperationalStatus | None = None


class InventoryResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    asset_code: str
    condition: EquipmentCondition
    operational_status: OperationalStatus
    created_at: datetime
