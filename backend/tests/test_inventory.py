import io
from datetime import timedelta

from PIL import Image

from app.models import Booking, BookingStatus, EquipmentCondition, OperationalStatus
from app.utils.dates import business_today
from tests.factories import make_unit


def test_admin_adds_and_lists_units(client, admin_headers, product):
    created = client.post(
        "/api/v1/admin/inventory",
        json={"product_id": product.id, "asset_code": " cam-001 "},
        headers=admin_headers,
    )

    assert created.status_code == 201
    assert created.json()["asset_code"] == "CAM-001"
    assert created.json()["condition"] == "EXCELLENT"
    assert created.json()["operational_status"] == "ACTIVE"
    listing = client.get("/api/v1/admin/inventory", headers=admin_headers).json()
    assert [unit["product_name"] for unit in listing] == ["Sony Alpha A6400"]


def test_duplicate_asset_code_and_unknown_product(client, admin_headers, product):
    payload = {"product_id": product.id, "asset_code": "CAM-001"}
    client.post("/api/v1/admin/inventory", json=payload, headers=admin_headers)

    assert client.post("/api/v1/admin/inventory", json=payload, headers=admin_headers).status_code == 409
    missing = {"product_id": 9999, "asset_code": "X-1"}
    assert client.post("/api/v1/admin/inventory", json=missing, headers=admin_headers).status_code == 404


def test_update_condition_and_status(client, admin_headers, db, product):
    unit = make_unit(db, product, "CAM-001")

    response = client.patch(
        f"/api/v1/admin/inventory/{unit.id}",
        json={"condition": "FAIR", "operational_status": "MAINTENANCE"},
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["condition"] == "FAIR"
    assert response.json()["operational_status"] == "MAINTENANCE"


def _add_booking(db, product, unit, customer, status, pickup_offset, return_offset):
    today = business_today()
    booking = Booking(
        booking_reference=f"RNT-{status.value}-{unit.id}",
        user_id=customer.id,
        product_id=product.id,
        inventory_unit_id=unit.id,
        pickup_date=today + timedelta(days=pickup_offset),
        return_date=today + timedelta(days=return_offset),
        rental_days=return_offset - pickup_offset,
        daily_price=product.daily_price,
        total_amount=product.daily_price * (return_offset - pickup_offset),
        status=status,
        idempotency_key=f"key-{status.value}-{unit.id}",
        request_fingerprint="x",
    )
    db.add(booking)
    db.commit()
    return booking


def test_cannot_take_unit_out_of_service_with_future_confirmed_booking(client, admin_headers, db, product, customer):
    unit = make_unit(db, product, "CAM-001")
    _add_booking(db, product, unit, customer, BookingStatus.CONFIRMED, 5, 8)

    for change in ({"operational_status": "MAINTENANCE"}, {"operational_status": "RETIRED"}, {"condition": "DAMAGED"}):
        response = client.patch(f"/api/v1/admin/inventory/{unit.id}", json=change, headers=admin_headers)
        assert response.status_code == 409, change
        assert "RNT-CONFIRMED" in response.json()["detail"]

    db.refresh(unit)
    assert unit.operational_status == OperationalStatus.ACTIVE and unit.condition == EquipmentCondition.EXCELLENT


def test_cannot_take_unit_out_of_service_while_rented_out(client, admin_headers, db, product, customer):
    unit = make_unit(db, product, "CAM-001")
    _add_booking(db, product, unit, customer, BookingStatus.PICKED_UP, -1, 2)

    response = client.patch(
        f"/api/v1/admin/inventory/{unit.id}", json={"operational_status": "MAINTENANCE"}, headers=admin_headers
    )
    assert response.status_code == 409


def test_finished_bookings_do_not_block_status_change(client, admin_headers, db, product, customer):
    unit = make_unit(db, product, "CAM-001")
    _add_booking(db, product, unit, customer, BookingStatus.RETURNED, -5, -2)
    _add_booking(db, product, unit, customer, BookingStatus.CANCELLED, 5, 8)

    response = client.patch(
        f"/api/v1/admin/inventory/{unit.id}", json={"operational_status": "RETIRED"}, headers=admin_headers
    )
    assert response.status_code == 200


def test_booking_cannot_reference_unit_of_another_product(db, category, product, customer):
    import pytest
    from sqlalchemy.exc import IntegrityError

    from tests.factories import make_product

    other_product = make_product(db, category, name="Other Camera")
    unit_of_other = make_unit(db, other_product, "OTH-001")

    with pytest.raises(IntegrityError):
        _add_booking(db, product, unit_of_other, customer, BookingStatus.CONFIRMED, 2, 4)


def _image_bytes(image_format: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "orange").save(buffer, format=image_format)
    return buffer.getvalue()


def test_upload_image_stores_file_and_serves_it(client, admin_headers, product):
    response = client.post(
        f"/api/v1/admin/products/{product.id}/image",
        files={"file": ("../../evil name.png", _image_bytes("PNG"), "image/png")},
        headers=admin_headers,
    )

    assert response.status_code == 200
    url = response.json()["image_url"]
    assert url.startswith("/uploads/products/") and url.endswith(".png")
    assert "evil" not in url and ".." not in url
    assert client.get(url).status_code == 200


def test_upload_rejects_non_images_wrong_formats_and_big_files(client, admin_headers, product):
    endpoint = f"/api/v1/admin/products/{product.id}/image"
    fake = {"file": ("shell.png", b"<?php echo 1; ?>", "image/png")}
    gif = {"file": ("a.gif", _image_bytes("GIF"), "image/gif")}
    huge = {"file": ("big.png", b"\x89PNG" + b"0" * (5 * 1024 * 1024 + 1), "image/png")}

    for files in (fake, gif, huge):
        assert client.post(endpoint, files=files, headers=admin_headers).status_code == 400


def test_upload_requires_admin(client, customer_headers, product):
    response = client.post(
        f"/api/v1/admin/products/{product.id}/image",
        files={"file": ("a.png", _image_bytes("PNG"), "image/png")},
        headers=customer_headers,
    )
    assert response.status_code == 403
