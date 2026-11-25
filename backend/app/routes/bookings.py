from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.booking import BookingStatus
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse, CancelRequest, QuoteRequest, QuoteResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/quote", response_model=QuoteResponse)
def quote(data: QuoteRequest, db: Session = Depends(get_db)) -> QuoteResponse:
    """Price and availability for a product and dates. Public, reserves nothing."""
    return booking_service.build_quote(db, data.product_id, data.pickup_date, data.return_date)


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingResponse:
    booking, created = booking_service.create_booking(db, current_user, data)
    if not created:
        response.status_code = status.HTTP_200_OK  # idempotent replay of an earlier checkout
    return booking_service.get_booking_response(db, booking.id)


@router.get("", response_model=list[BookingResponse])
def list_my_bookings(
    status_filter: BookingStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BookingResponse]:
    return booking_service.list_customer_bookings(db, current_user, status_filter)


@router.get("/{booking_id}", response_model=BookingResponse)
def get_my_booking(
    booking_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BookingResponse:
    return booking_service.get_booking_response(db, booking_id, owner=current_user)


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_my_booking(
    booking_id: int,
    data: CancelRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BookingResponse:
    booking_service.cancel_booking(db, booking_id, current_user, data.reason if data else None, as_admin=False)
    return booking_service.get_booking_response(db, booking_id, owner=current_user)
