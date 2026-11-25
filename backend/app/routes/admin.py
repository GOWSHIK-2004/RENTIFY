from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.schemas.product import ProductResponse
from app.services import image_service, product_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/products/{product_id}/image", response_model=ProductResponse)
def upload_product_image(product_id: int, file: UploadFile, db: Session = Depends(get_db)) -> ProductResponse:
    product = product_service.get_product_or_404(db, product_id)
    image_service.save_product_image(db, product, file)
    return product_service.get_product_response(db, product_id, include_inactive=True)
