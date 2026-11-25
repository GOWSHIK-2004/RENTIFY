from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.booking import BookingStatus
from app.models.payment import PaymentStatus


class MonthlyRevenue(BaseModel):
    month: str  # "2026-11"
    revenue: Decimal


class StatusCount(BaseModel):
    status: BookingStatus
    count: int


class TopProduct(BaseModel):
    product_id: int
    name: str
    bookings: int


class DashboardResponse(BaseModel):
    active_products: int
    inventory_units: int
    confirmed_bookings: int
    active_rentals: int
    completed_bookings: int
    overdue_rentals: int
    total_revenue: Decimal
    monthly_revenue: list[MonthlyRevenue]
    status_distribution: list[StatusCount]
    top_products: list[TopProduct]


class CustomerSummary(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: datetime
    booking_count: int


class CustomerListResponse(BaseModel):
    items: list[CustomerSummary]
    total: int
    page: int
    page_size: int
    pages: int


class PaymentSummary(BaseModel):
    id: int
    transaction_reference: str
    booking_reference: str
    customer_name: str
    product_name: str
    amount: Decimal
    status: PaymentStatus
    created_at: datetime


class PaymentListResponse(BaseModel):
    items: list[PaymentSummary]
    total: int
    page: int
    page_size: int
    pages: int
