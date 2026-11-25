import itertools
from datetime import timedelta
from decimal import Decimal

from app.models import (
    Booking,
    BookingStatus,
    Category,
    InventoryUnit,
    Payment,
    PaymentStatus,
    Product,
    User,
    UserRole,
)
from app.utils.dates import business_today
from app.utils.security import create_access_token, hash_password

PASSWORD = "correct-horse-battery"


def make_user(db, email: str, role: UserRole = UserRole.CUSTOMER, name: str = "Test User") -> User:
    user = User(full_name=name, email=email, password_hash=hash_password(PASSWORD), role=role)
    db.add(user)
    db.commit()
    return user


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


def make_category(db, name: str = "Cameras", slug: str | None = None, is_active: bool = True) -> Category:
    category = Category(name=name, slug=slug or name.lower().replace(" ", "-"), is_active=is_active)
    db.add(category)
    db.commit()
    return category


def make_product(db, category: Category, name: str = "Sony Alpha A6400", brand: str = "Sony",
                 daily_price: str = "899.00", **extra) -> Product:
    product = Product(
        category_id=category.id,
        name=name,
        brand=brand,
        model=extra.pop("model", name),
        short_description="Short description",
        description="Long description",
        daily_price=Decimal(daily_price),
        specifications={"Sensor": "APS-C"},
        **extra,
    )
    db.add(product)
    db.commit()
    return product


def make_unit(db, product: Product, asset_code: str, **extra) -> InventoryUnit:
    unit = InventoryUnit(product_id=product.id, asset_code=asset_code, **extra)
    db.add(unit)
    db.commit()
    return unit


_booking_numbers = itertools.count(1)


def make_booking(db, user, product, unit, status=BookingStatus.CONFIRMED, pickup_offset: int = 5,
                 return_offset: int = 8) -> Booking:
    """Insert a booking directly. Offsets are days relative to today (Asia/Kolkata)."""
    number = next(_booking_numbers)
    today = business_today()
    days = return_offset - pickup_offset
    total = product.daily_price * days
    booking = Booking(
        booking_reference=f"RNT-TEST{number:04d}",
        user_id=user.id,
        product_id=product.id,
        inventory_unit_id=unit.id,
        pickup_date=today + timedelta(days=pickup_offset),
        return_date=today + timedelta(days=return_offset),
        rental_days=days,
        daily_price=product.daily_price,
        total_amount=total,
        status=status,
        idempotency_key=f"seed-{number}",
        request_fingerprint="seed",
    )
    booking.payment = Payment(transaction_reference=f"TXN-TEST{number:04d}", amount=total, status=PaymentStatus.SUCCESS)
    db.add(booking)
    db.commit()
    return booking
