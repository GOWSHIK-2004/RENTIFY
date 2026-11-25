from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.booking import BookingStatus
from app.models.payment import PaymentStatus
from app.models.user import User
from app.schemas.admin import CustomerListResponse, DashboardResponse, PaymentListResponse
from app.schemas.booking import BookingListResponse, BookingResponse, CancelRequest, ReturnRequest
from app.schemas.product import ProductResponse
from app.services import admin_service, booking_service, image_service, product_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    return admin_service.build_dashboard(db)


@router.get("/users", response_model=CustomerListResponse)
def list_customers(
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> CustomerListResponse:
    return admin_service.list_customers(db, search, page, page_size)


@router.get("/payments", response_model=PaymentListResponse)
def list_payments(
    status_filter: PaymentStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaymentListResponse:
    return admin_service.list_payments(db, status_filter, page, page_size)


@router.get("/bookings", response_model=BookingListResponse)
def list_bookings(
    status_filter: BookingStatus | None = None,
    overdue: bool = False,
    search: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BookingListResponse:
    return booking_service.list_admin_bookings(db, status_filter, overdue, search, page, page_size)


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)) -> BookingResponse:
    return booking_service.get_booking_response(db, booking_id)


@router.post("/bookings/{booking_id}/pickup", response_model=BookingResponse)
def pickup_booking(booking_id: int, db: Session = Depends(get_db)) -> BookingResponse:
    booking_service.pickup_booking(db, booking_id)
    return booking_service.get_booking_response(db, booking_id)


@router.post("/bookings/{booking_id}/return", response_model=BookingResponse)
def return_booking(booking_id: int, data: ReturnRequest | None = None, db: Session = Depends(get_db)) -> BookingResponse:
    booking_service.return_booking(db, booking_id, data.condition if data else None)
    return booking_service.get_booking_response(db, booking_id)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    data: CancelRequest | None = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BookingResponse:
    booking_service.cancel_booking(db, booking_id, admin, data.reason if data else None, as_admin=True)
    return booking_service.get_booking_response(db, booking_id)


@router.post("/products/{product_id}/image", response_model=ProductResponse)
def upload_product_image(product_id: int, file: UploadFile, db: Session = Depends(get_db)) -> ProductResponse:
    product = product_service.get_product_or_404(db, product_id)
    image_service.save_product_image(db, product, file)
    return product_service.get_product_response(db, product_id, include_inactive=True)
