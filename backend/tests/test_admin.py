from decimal import Decimal

from app.models import BookingStatus, PaymentStatus
from tests.factories import make_booking, make_unit, make_user

API = "/api/v1"


def test_admin_overview_endpoints_reject_customers_and_anonymous(client, customer_headers):
    for path in ("/admin/dashboard", "/admin/users", "/admin/payments"):
        assert client.get(API + path).status_code == 401
        assert client.get(API + path, headers=customer_headers).status_code == 403


def test_dashboard_numbers_come_from_the_database(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    make_unit(db, product, "CAM-002")
    make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 5, 8)  # 3 x 899 = 2697
    make_booking(db, customer, product, unit, BookingStatus.PICKED_UP, -5, -1)  # overdue, 4 x 899 = 3596
    make_booking(db, customer, product, unit, BookingStatus.RETURNED, -20, -18)  # 2 x 899 = 1798
    cancelled = make_booking(db, customer, product, unit, BookingStatus.CANCELLED, 30, 32)
    cancelled.payment.status = PaymentStatus.REFUNDED  # refunded money is not revenue
    db.commit()

    body = client.get(f"{API}/admin/dashboard", headers=admin_headers).json()

    assert body["active_products"] == 1 and body["inventory_units"] == 2
    assert body["confirmed_bookings"] == 1 and body["active_rentals"] == 1
    assert body["completed_bookings"] == 1 and body["overdue_rentals"] == 1
    assert Decimal(body["total_revenue"]) == Decimal("2697") + Decimal("3596") + Decimal("1798")
    counts = {row["status"]: row["count"] for row in body["status_distribution"]}
    assert counts == {"CONFIRMED": 1, "PICKED_UP": 1, "RETURNED": 1, "CANCELLED": 1}
    assert body["top_products"] == [{"product_id": product.id, "name": "Sony Alpha A6400", "bookings": 3}]
    assert len(body["monthly_revenue"]) == 12
    assert sum(Decimal(m["revenue"]) for m in body["monthly_revenue"]) == Decimal(body["total_revenue"])


def test_dashboard_on_an_empty_database(client, admin_headers):
    body = client.get(f"{API}/admin/dashboard", headers=admin_headers).json()

    assert body["total_revenue"] == "0.00" and body["top_products"] == []
    assert [row["count"] for row in body["status_distribution"]] == [0, 0, 0, 0]


def test_customer_list_excludes_admins_and_hides_password_hashes(client, db, customer, admin, admin_headers):
    response = client.get(f"{API}/admin/users", headers=admin_headers)

    assert response.status_code == 200
    items = response.json()["items"]
    assert [u["email"] for u in items] == ["customer@example.com"]
    assert "password_hash" not in items[0] and "role" not in items[0]


def test_customer_list_search_and_booking_count(client, db, product, customer, admin_headers):
    make_user(db, "other@example.com", name="Olivia Other")
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 5, 8)

    found = client.get(f"{API}/admin/users", params={"search": "casey"}, headers=admin_headers).json()

    assert found["total"] == 1 and found["items"][0]["booking_count"] == 1


def test_payment_list_shows_refund_status(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 5, 8)
    cancelled = make_booking(db, customer, product, unit, BookingStatus.CANCELLED, 20, 22)
    cancelled.payment.status = PaymentStatus.REFUNDED
    db.commit()

    everything = client.get(f"{API}/admin/payments", headers=admin_headers).json()
    refunded = client.get(f"{API}/admin/payments", params={"status_filter": "REFUNDED"}, headers=admin_headers).json()

    assert everything["total"] == 2
    assert [p["status"] for p in refunded["items"]] == ["REFUNDED"]
    assert refunded["items"][0]["booking_reference"] == cancelled.booking_reference
    assert refunded["items"][0]["customer_name"] == "Casey Customer"
