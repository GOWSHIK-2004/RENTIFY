"""Demo data for Rentify. Safe to run repeatedly: every record is looked up first.

    python seed.py

Creates categories, ~20 products with placeholder images, inventory units,
the administrator (from ADMIN_EMAIL / ADMIN_PASSWORD), sample customers,
bookings in every state, payments and reviews. Existing rows are never
modified or deleted, so real customer data and admin edits are preserved.
"""
import logging
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import (
    Booking,
    BookingStatus,
    Category,
    InventoryUnit,
    Payment,
    PaymentStatus,
    Product,
    Review,
    User,
    UserRole,
)
from app.utils.dates import business_today
from app.utils.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("seed")

CUSTOMER_PASSWORD = "Customer@123"  # demo accounts only

CATEGORIES = [
    ("Cameras & Photography", "cameras", "Mirrorless cameras and action cameras for trips, shoots and content creation.", "#F97316"),
    ("Gaming Consoles", "gaming-consoles", "Current-generation consoles for a weekend of play.", "#2563EB"),
    ("Laptops & Computers", "laptops", "Powerful laptops for work, study and creative projects.", "#0F766E"),
    ("Drones", "drones", "Compact camera drones for aerial photography and video.", "#7C3AED"),
    ("Musical Instruments", "musical-instruments", "Keyboards, guitars and drums for practice, gigs and recording.", "#BE123C"),
    ("Audio Equipment", "audio-equipment", "Microphones, interfaces and speakers for events and studios.", "#0369A1"),
    ("Projectors", "projectors", "Bright projectors for presentations, events and movie nights.", "#B45309"),
]

# slug, name, brand, model, category, daily price, units, featured, short description, specs
PRODUCTS = [
    ("sony-alpha-a6400", "Sony Alpha A6400", "Sony", "ILCE-6400", "cameras", "899", 3, True,
     "Compact mirrorless camera suitable for photography, video recording and content creation.",
     {"Sensor": "APS-C", "Resolution": "24.2 MP", "Video": "4K", "Lens mount": "Sony E"}),
    ("canon-eos-r50", "Canon EOS R50", "Canon", "EOS R50", "cameras", "799", 2, True,
     "Lightweight mirrorless camera with fast autofocus, ideal for travel and vlogging.",
     {"Sensor": "APS-C CMOS", "Resolution": "24.2 MP", "Video": "4K 30p", "Lens mount": "Canon RF"}),
    ("gopro-hero12-black", "GoPro HERO12 Black", "GoPro", "HERO12", "cameras", "499", 3, False,
     "Rugged waterproof action camera with HyperSmooth stabilisation.",
     {"Video": "5.3K 60p", "Photo": "27 MP", "Waterproof": "10 m", "Stabilisation": "HyperSmooth 6.0"}),
    ("nikon-z-fc", "Nikon Z fc", "Nikon", "Z fc", "cameras", "849", 1, False,
     "Retro-styled mirrorless camera with modern performance.",
     {"Sensor": "APS-C CMOS", "Resolution": "20.9 MP", "Video": "4K 30p", "Lens mount": "Nikon Z"}),
    ("playstation-5", "PlayStation 5", "Sony", "CFI-1208A", "gaming-consoles", "699", 3, True,
     "Sony's flagship console with a fast SSD and DualSense controller.",
     {"Storage": "825 GB SSD", "Output": "4K up to 120 Hz", "Controllers": "1 DualSense", "Disc drive": "Yes"}),
    ("xbox-series-x", "Xbox Series X", "Microsoft", "Series X", "gaming-consoles", "649", 2, False,
     "Powerful 4K console with a large game library.",
     {"Storage": "1 TB SSD", "Output": "4K up to 120 Hz", "Controllers": "1 wireless", "Disc drive": "Yes"}),
    ("nintendo-switch-oled", "Nintendo Switch OLED", "Nintendo", "HEG-001", "gaming-consoles", "399", 2, False,
     "Handheld and TV-ready console with a vibrant OLED screen.",
     {"Display": "7-inch OLED", "Storage": "64 GB", "Controllers": "2 Joy-Con", "Battery": "4.5 to 9 hours"}),
    ("dell-xps-13", "Dell XPS 13", "Dell", "XPS 9315", "laptops", "1199", 2, True,
     "Premium ultraportable laptop with an edge-to-edge display.",
     {"Processor": "Intel Core i7", "Memory": "16 GB", "Storage": "512 GB SSD", "Display": "13.4-inch FHD+"}),
    ("asus-rog-zephyrus-g14", "ASUS ROG Zephyrus G14", "ASUS", "GA402", "laptops", "1499", 2, False,
     "Compact gaming and creator laptop with a dedicated GPU.",
     {"Processor": "AMD Ryzen 9", "Graphics": "RTX 4060", "Memory": "16 GB", "Display": "14-inch QHD 120 Hz"}),
    ("macbook-air-m2", "MacBook Air M2", "Apple", "MLY33", "laptops", "1299", 2, False,
     "Thin, silent laptop with all-day battery life.",
     {"Chip": "Apple M2", "Memory": "8 GB", "Storage": "256 GB SSD", "Display": "13.6-inch Liquid Retina"}),
    ("dji-mini-4-pro", "DJI Mini 4 Pro", "DJI", "Mini 4 Pro", "drones", "1499", 2, True,
     "Under-250 g drone with 4K HDR video and obstacle sensing.",
     {"Video": "4K 60p HDR", "Flight time": "34 minutes", "Weight": "< 249 g", "Range": "20 km"}),
    ("dji-air-3", "DJI Air 3", "DJI", "Air 3", "drones", "1799", 1, False,
     "Dual-camera drone for versatile aerial shots.",
     {"Cameras": "Wide + 3x tele", "Video": "4K 100p", "Flight time": "46 minutes", "Range": "20 km"}),
    ("yamaha-psr-e373", "Yamaha PSR-E373 Keyboard", "Yamaha", "PSR-E373", "musical-instruments", "599", 2, False,
     "61-key portable keyboard with hundreds of voices and styles.",
     {"Keys": "61 touch-sensitive", "Voices": "622", "Polyphony": "48 notes", "Connectivity": "USB, headphone"}),
    ("fender-player-stratocaster", "Fender Player Stratocaster", "Fender", "Player Strat", "musical-instruments", "699", 1, False,
     "Classic electric guitar with the iconic Stratocaster tone.",
     {"Body": "Alder", "Pickups": "3 single-coil", "Neck": "Maple, 22 frets", "Scale": "25.5 inch"}),
    ("roland-td-1dmk", "Roland TD-1DMK Electronic Drums", "Roland", "TD-1DMK", "musical-instruments", "899", 1, False,
     "Compact electronic drum kit with mesh heads for quiet practice.",
     {"Kit sounds": "15", "Pads": "Mesh snare and toms", "Pedals": "Kick + hi-hat", "Output": "Headphone, USB"}),
    ("shure-sm58", "Shure SM58 Microphone", "Shure", "SM58", "audio-equipment", "199", 4, True,
     "Industry-standard dynamic vocal microphone.",
     {"Type": "Dynamic", "Pattern": "Cardioid", "Connector": "XLR", "Frequency": "50 Hz to 15 kHz"}),
    ("focusrite-scarlett-2i2", "Focusrite Scarlett 2i2", "Focusrite", "Scarlett 2i2 (4th Gen)", "audio-equipment", "299", 2, False,
     "USB audio interface for home recording and streaming.",
     {"Inputs": "2 mic/line", "Resolution": "24-bit / 192 kHz", "Connection": "USB-C", "Preamps": "Studio-quality"}),
    ("jbl-partybox-310", "JBL PartyBox 310", "JBL", "PartyBox 310", "audio-equipment", "799", 2, False,
     "Portable party speaker with light show and long battery life.",
     {"Output": "240 W", "Battery": "18 hours", "Inputs": "Mic + guitar", "Protection": "IPX4 splash-proof"}),
    ("epson-eb-x49", "Epson EB-X49 Projector", "Epson", "EB-X49", "projectors", "999", 2, True,
     "Bright XGA projector for classrooms, meetings and events.",
     {"Brightness": "3600 lumens", "Resolution": "XGA 1024x768", "Contrast": "16,000:1", "Inputs": "HDMI, VGA, USB"}),
    ("benq-th585", "BenQ TH585 Projector", "BenQ", "TH585", "projectors", "1199", 1, False,
     "Full HD home-cinema projector with low input lag for gaming.",
     {"Brightness": "3500 lumens", "Resolution": "Full HD 1080p", "Contrast": "20,000:1", "Inputs": "2x HDMI, USB"}),
]

CUSTOMERS = [
    ("Priya Sharma", "priya.sharma@example.com"),
    ("Rahul Verma", "rahul.verma@example.com"),
    ("Ananya Iyer", "ananya.iyer@example.com"),
    ("Karthik Nair", "karthik.nair@example.com"),
]

# reference suffix, customer email, product slug, unit index, status, pickup offset, return offset (days from today)
BOOKINGS = [
    # Completed rentals (these can be reviewed)
    ("0001", "priya.sharma@example.com", "sony-alpha-a6400", 0, BookingStatus.RETURNED, -30, -27),
    ("0002", "rahul.verma@example.com", "playstation-5", 0, BookingStatus.RETURNED, -20, -17),
    ("0003", "ananya.iyer@example.com", "dji-mini-4-pro", 0, BookingStatus.RETURNED, -45, -42),
    ("0004", "karthik.nair@example.com", "shure-sm58", 0, BookingStatus.RETURNED, -12, -10),
    ("0005", "priya.sharma@example.com", "dell-xps-13", 0, BookingStatus.RETURNED, -25, -22),
    ("0006", "rahul.verma@example.com", "gopro-hero12-black", 0, BookingStatus.RETURNED, -60, -57),
    ("0007", "ananya.iyer@example.com", "epson-eb-x49", 0, BookingStatus.RETURNED, -15, -12),
    ("0008", "karthik.nair@example.com", "yamaha-psr-e373", 0, BookingStatus.RETURNED, -8, -6),
    # Rented out right now, and one overdue (picked up, not returned, past its return date)
    ("0009", "ananya.iyer@example.com", "asus-rog-zephyrus-g14", 0, BookingStatus.PICKED_UP, -1, 2),
    ("0010", "karthik.nair@example.com", "canon-eos-r50", 0, BookingStatus.PICKED_UP, -6, -2),
    # Upcoming confirmed bookings
    ("0011", "priya.sharma@example.com", "nintendo-switch-oled", 0, BookingStatus.CONFIRMED, 3, 6),
    ("0012", "rahul.verma@example.com", "dji-air-3", 0, BookingStatus.CONFIRMED, 7, 10),
    ("0013", "ananya.iyer@example.com", "focusrite-scarlett-2i2", 0, BookingStatus.CONFIRMED, 5, 7),
    ("0014", "karthik.nair@example.com", "xbox-series-x", 0, BookingStatus.CONFIRMED, 10, 14),
    ("0015", "rahul.verma@example.com", "sony-alpha-a6400", 0, BookingStatus.CONFIRMED, 4, 7),
    ("0016", "priya.sharma@example.com", "benq-th585", 0, BookingStatus.CONFIRMED, 2, 4),
    # Cancelled before pickup (payment refunded)
    ("0017", "karthik.nair@example.com", "fender-player-stratocaster", 0, BookingStatus.CANCELLED, 9, 11),
]

# booking suffix -> (rating, comment). Only RETURNED bookings may be reviewed.
REVIEWS = {
    "0001": (5, "Sharp photos and great battery life. Pickup was quick and easy."),
    "0002": (5, "Perfect for the weekend. Console arrived clean and fully working."),
    "0003": (4, "Smooth flights and beautiful footage. Wish I had booked a day longer."),
    "0004": (5, "Great microphone for our event. Exactly as described."),
    "0005": (4, "Fast and light. Handled my video edits without trouble."),
    "0007": (3, "Bright picture, but the bag was a little worn."),
}

IST = ZoneInfo("Asia/Kolkata")


def get_or_create_category(db: Session, name: str, slug: str, description: str) -> Category:
    category = db.scalar(select(Category).where(Category.slug == slug))
    if category is None:
        category = Category(name=name, slug=slug, description=description)
        db.add(category)
        db.flush()
        log.info("  + category %s", name)
    return category


def make_placeholder_image(upload_dir, slug: str, title: str, subtitle: str, color: str) -> str:
    """Draw a simple branded placeholder so the demo needs no downloaded photos."""
    relative = f"products/seed-{slug}.png"
    target = upload_dir / relative
    if target.exists():
        return relative
    target.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (800, 600), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 420, 800, 600), fill=(15, 23, 42))
    draw.text((40, 440), title, fill="white", font=ImageFont.load_default(size=44))
    draw.text((40, 505), subtitle, fill=(203, 213, 225), font=ImageFont.load_default(size=26))
    draw.text((40, 40), "RENTIFY DEMO", fill="white", font=ImageFont.load_default(size=22))
    image.save(target, "PNG")
    return relative


def seed_catalog(db: Session) -> dict[str, list[InventoryUnit]]:
    upload_dir = get_settings().upload_dir
    categories = {
        slug: get_or_create_category(db, name, slug, description) for name, slug, description, _ in CATEGORIES
    }
    colors = {slug: color for _, slug, _, color in CATEGORIES}
    prefixes = {"cameras": "CAM", "gaming-consoles": "GAM", "laptops": "LAP", "drones": "DRN",
                "musical-instruments": "MUS", "audio-equipment": "AUD", "projectors": "PRJ"}
    counters = {slug: 0 for slug in categories}
    now = datetime.now(UTC)
    units_by_product: dict[str, list[InventoryUnit]] = {}

    for index, (slug, name, brand, model, category_slug, price, unit_count, featured, short, specs) in enumerate(PRODUCTS):
        product = db.scalar(select(Product).where(Product.name == name))
        if product is None:
            product = Product(
                category_id=categories[category_slug].id,
                name=name,
                brand=brand,
                model=model,
                short_description=short,
                description=f"{short} Rented daily from Rentify's own inventory, inspected and cleaned before every pickup.",
                daily_price=Decimal(price),
                specifications=specs,
                is_featured=featured,
                created_at=now - timedelta(hours=len(PRODUCTS) - index),
            )
            db.add(product)
            db.flush()
            log.info("  + product %s", name)
        # Create the placeholder when the product has no image, or when its seed image file is
        # missing from disk (for example a fresh uploads volume). Admin-uploaded images are left alone.
        seed_image = f"products/seed-{slug}.png"
        if product.image_path is None or (product.image_path == seed_image and not (upload_dir / seed_image).exists()):
            product.image_path = make_placeholder_image(upload_dir, slug, name, brand, colors[category_slug])

        units = []
        for _ in range(unit_count):
            counters[category_slug] += 1
            code = f"{prefixes[category_slug]}-{counters[category_slug]:03d}"
            unit = db.scalar(select(InventoryUnit).where(InventoryUnit.asset_code == code))
            if unit is None:
                unit = InventoryUnit(product_id=product.id, asset_code=code)
                db.add(unit)
                db.flush()
            units.append(unit)
        units_by_product[slug] = units
    return units_by_product


def seed_users(db: Session) -> dict[str, User]:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD in backend/.env before seeding.")

    admin_email = settings.admin_email.strip().lower()
    try:
        # Same validation the login form applies, so the admin can actually sign in.
        TypeAdapter(EmailStr).validate_python(admin_email)
    except ValidationError as error:
        raise SystemExit(f"ADMIN_EMAIL is not a valid email address: {error.errors()[0]['msg']}")
    admin = db.scalar(select(User).where(User.email == admin_email))
    if admin is None:
        db.add(User(full_name="Rentify Admin", email=admin_email,
                    password_hash=hash_password(settings.admin_password), role=UserRole.ADMIN))
        log.info("  + administrator %s", admin_email)
    elif admin.role != UserRole.ADMIN:
        admin.role = UserRole.ADMIN  # password is left untouched

    customers = {}
    for full_name, email in CUSTOMERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(full_name=full_name, email=email, password_hash=hash_password(CUSTOMER_PASSWORD))
            db.add(user)
            log.info("  + customer %s", email)
        customers[email] = user
    db.flush()
    return customers


def seed_bookings(db: Session, customers: dict[str, User], units_by_product: dict[str, list[InventoryUnit]]) -> None:
    today = business_today()
    products = {p.name: p for p in db.scalars(select(Product))}
    product_by_slug = {slug: products[name] for slug, name, *_ in PRODUCTS}

    for suffix, email, slug, unit_index, status, pickup_offset, return_offset in BOOKINGS:
        reference = f"RNT-SEED{suffix}"
        booking = db.scalar(select(Booking).where(Booking.booking_reference == reference))
        if booking is not None:
            continue

        product = product_by_slug[slug]
        unit = units_by_product[slug][unit_index]
        pickup_date = today + timedelta(days=pickup_offset)
        return_date = today + timedelta(days=return_offset)
        days = return_offset - pickup_offset
        total = product.daily_price * days
        booked_at = datetime.combine(pickup_date - timedelta(days=3), time(12, 0), tzinfo=IST)

        booking = Booking(
            booking_reference=reference,
            user_id=customers[email].id,
            product_id=product.id,
            inventory_unit_id=unit.id,
            pickup_date=pickup_date,
            return_date=return_date,
            rental_days=days,
            daily_price=product.daily_price,
            total_amount=total,
            status=status,
            idempotency_key=f"seed-{suffix}",
            request_fingerprint="seed",
            created_at=booked_at,
        )
        if status in (BookingStatus.PICKED_UP, BookingStatus.RETURNED):
            booking.actual_pickup_at = datetime.combine(pickup_date, time(10, 0), tzinfo=IST)
        if status == BookingStatus.RETURNED:
            booking.actual_return_at = datetime.combine(return_date, time(18, 0), tzinfo=IST)
        if status == BookingStatus.CANCELLED:
            booking.cancellation_reason = "Plans changed"
        booking.payment = Payment(
            transaction_reference=f"TXN-SEED{suffix}",
            amount=total,
            status=PaymentStatus.REFUNDED if status == BookingStatus.CANCELLED else PaymentStatus.SUCCESS,
            created_at=booked_at,
        )
        db.add(booking)
        db.flush()
        log.info("  + booking %s (%s, %s)", reference, product.name, status.value)

        if suffix in REVIEWS and status == BookingStatus.RETURNED:
            rating, comment = REVIEWS[suffix]
            db.add(Review(user_id=booking.user_id, product_id=product.id, booking_id=booking.id,
                          rating=rating, comment=comment))


def main() -> None:
    with SessionLocal() as db:
        try:
            log.info("Seeding Rentify demo data...")
            units = seed_catalog(db)
            customers = seed_users(db)
            seed_bookings(db, customers, units)
            db.commit()  # everything or nothing
        except Exception:
            db.rollback()
            raise
    log.info("Done. Customer demo password: %s", CUSTOMER_PASSWORD)


if __name__ == "__main__":
    main()
