import threading
import time
import uuid
from datetime import timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Booking, BookingStatus, EquipmentCondition, OperationalStatus, Payment, PaymentStatus
from app.services.pricing_service import calculate_total
from app.services.product_service import lock_product
from app.utils.dates import business_today
from tests.factories import auth_headers, make_booking, make_unit, make_user

API = "/api/v1"


def day(offset: int) -> str:
    return (business_today() + timedelta(days=offset)).isoformat()


def checkout(client, headers, product, pickup=5, days=3, key=None, outcome="success", total=None):
    """POST /bookings the way the checkout page does."""
    expected = total if total is not None else str(product.daily_price * days)
    return client.post(
        f"{API}/bookings",
        headers=headers,
        json={
            "product_id": product.id,
            "pickup_date": day(pickup),
            "return_date": day(pickup + days),
            "expected_total": expected,
            "idempotency_key": key or uuid.uuid4().hex,
            "payment_outcome": outcome,
        },
    )


def quote(client, product, pickup=5, days=3):
    return client.get(
        f"{API}/products/{product.id}/availability",
        params={"pickup_date": day(pickup), "return_date": day(pickup + days)},
    )


# ---------------------------------------------------------------- pricing & dates
def test_price_calculation_uses_decimal_and_excludes_return_day():
    assert calculate_total(Decimal("899.00"), 3) == Decimal("2697.00")
    assert calculate_total(Decimal("0.10"), 3) == Decimal("0.30")  # float math would give 0.30000000000000004


def test_quote_returns_duration_price_and_availability(client, product, db):
    make_unit(db, product, "CAM-001")

    body = quote(client, product).json()

    assert body["rental_days"] == 3
    assert body["daily_price"] == "899.00"
    assert body["total_amount"] == "2697.00"
    assert body["available"] is True and body["available_units"] == 1


def test_quote_post_endpoint_matches_get(client, product, db):
    make_unit(db, product, "CAM-001")
    payload = {"product_id": product.id, "pickup_date": day(2), "return_date": day(4)}

    body = client.post(f"{API}/bookings/quote", json=payload).json()

    assert body["total_amount"] == "1798.00"


def test_invalid_rental_dates_are_rejected(client, product, db):
    make_unit(db, product, "CAM-001")
    cases = {
        "past pickup": (-1, 2),
        "same day": (3, 3),
        "return before pickup": (5, 3),
        "longer than 30 days": (1, 32),
    }
    for name, (pickup, return_) in cases.items():
        response = client.get(
            f"{API}/products/{product.id}/availability",
            params={"pickup_date": day(pickup), "return_date": day(return_)},
        )
        assert response.status_code == 400, name


def test_thirty_day_and_one_day_rentals_are_valid(client, product, db):
    make_unit(db, product, "CAM-001")
    assert quote(client, product, pickup=1, days=30).status_code == 200
    assert quote(client, product, pickup=0, days=1).status_code == 200


# ---------------------------------------------------------------- availability rules
def test_product_without_units_is_unavailable(client, product):
    body = quote(client, product).json()
    assert body["available"] is False and body["available_units"] == 0


def test_units_out_of_service_or_damaged_are_not_available(client, product, db):
    make_unit(db, product, "CAM-001", operational_status=OperationalStatus.MAINTENANCE)
    make_unit(db, product, "CAM-002", operational_status=OperationalStatus.RETIRED)
    make_unit(db, product, "CAM-003", condition=EquipmentCondition.DAMAGED)
    make_unit(db, product, "CAM-004", condition=EquipmentCondition.FAIR)

    assert quote(client, product).json()["available_units"] == 1


def test_overlapping_bookings_block_and_adjacent_ones_do_not(client, product, db, customer):
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, pickup_offset=10, return_offset=14)

    overlap = quote(client, product, pickup=12, days=4).json()  # 12-16 overlaps 10-14
    inside = quote(client, product, pickup=11, days=2).json()
    contains = quote(client, product, pickup=9, days=7).json()
    starts_on_return_day = quote(client, product, pickup=14, days=3).json()  # 14-17 touches 10-14
    ends_on_pickup_day = quote(client, product, pickup=7, days=3).json()  # 7-10 touches 10-14

    assert [overlap["available"], inside["available"], contains["available"]] == [False, False, False]
    assert starts_on_return_day["available"] is True
    assert ends_on_pickup_day["available"] is True


def test_cancelled_and_returned_bookings_do_not_block(client, product, db, customer):
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, customer, product, unit, BookingStatus.CANCELLED, 5, 8)
    make_booking(db, customer, product, unit, BookingStatus.RETURNED, 5, 8)

    assert quote(client, product, pickup=5, days=3).json()["available"] is True


def test_overdue_unit_is_excluded_and_future_booking_is_flagged(client, product, db, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, customer, product, unit, BookingStatus.PICKED_UP, pickup_offset=-5, return_offset=-1)
    waiting = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, pickup_offset=0, return_offset=2)

    assert quote(client, product, pickup=20, days=2).json()["available"] is False

    flagged = client.get(f"{API}/admin/bookings/{waiting.id}", headers=admin_headers).json()
    overdue_list = client.get(f"{API}/admin/bookings", params={"overdue": True}, headers=admin_headers).json()
    assert flagged["affected_by_overdue"] is True
    assert [b["is_overdue"] for b in overdue_list["items"]] == [True]


def test_inactive_product_cannot_be_quoted_or_booked(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    product.is_active = False
    db.commit()

    assert quote(client, product).status_code == 404
    assert checkout(client, customer_headers, product).status_code == 404


# ---------------------------------------------------------------- checkout
def test_successful_checkout_creates_booking_unit_and_payment_together(client, db, product, customer, customer_headers):
    make_unit(db, product, "CAM-001")

    response = checkout(client, customer_headers, product)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "CONFIRMED"
    assert body["booking_reference"].startswith("RNT-")
    assert body["asset_code"] == "CAM-001"
    assert body["rental_days"] == 3
    assert body["daily_price"] == "899.00" and body["total_amount"] == "2697.00"
    assert body["payment_status"] == "SUCCESS"
    assert db.query(Booking).count() == 1
    payment = db.query(Payment).one()
    assert payment.amount == Decimal("2697.00") and payment.status == PaymentStatus.SUCCESS
    assert payment.booking_id == body["id"]


def test_failed_payment_creates_nothing_and_reserves_nothing(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")

    response = checkout(client, customer_headers, product, outcome="failure")

    assert response.status_code == 402
    assert db.query(Booking).count() == 0 and db.query(Payment).count() == 0
    assert quote(client, product).json()["available"] is True
    assert checkout(client, customer_headers, product).status_code == 201  # unit is still free


def test_checkout_requires_login(client, product, db):
    make_unit(db, product, "CAM-001")
    response = client.post(f"{API}/bookings", json={})
    assert response.status_code == 401


def test_checkout_validates_dates(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    assert checkout(client, customer_headers, product, pickup=-2, days=3).status_code == 400
    assert checkout(client, customer_headers, product, pickup=5, days=31).status_code == 400
    assert db.query(Booking).count() == 0


def test_booking_price_is_a_snapshot_and_frontend_total_is_not_trusted(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    booking_id = checkout(client, customer_headers, product).json()["id"]

    product.daily_price = Decimal("1500.00")
    db.commit()

    stored = client.get(f"{API}/bookings/{booking_id}", headers=customer_headers).json()
    assert stored["daily_price"] == "899.00" and stored["total_amount"] == "2697.00"


def test_price_change_requires_reconfirmation(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    stale_total = "2697.00"
    product.daily_price = Decimal("1000.00")
    db.commit()

    response = checkout(client, customer_headers, product, total=stale_total)

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "PRICE_CHANGED" and detail["total_amount"] == "3000.00"
    assert db.query(Booking).count() == 0
    assert checkout(client, customer_headers, product, total="3000.00").status_code == 201


def test_two_units_allow_two_bookings_and_a_third_conflicts(client, db, product):
    make_unit(db, product, "CAM-001")
    make_unit(db, product, "CAM-002")
    people = [make_user(db, f"user{i}@example.com") for i in range(3)]

    first = checkout(client, auth_headers(people[0]), product)
    second = checkout(client, auth_headers(people[1]), product)
    third = checkout(client, auth_headers(people[2]), product)

    assert [first.status_code, second.status_code, third.status_code] == [201, 201, 409]
    assert {first.json()["asset_code"], second.json()["asset_code"]} == {"CAM-001", "CAM-002"}


def test_unavailable_at_confirmation_returns_409(client, db, product, customer, customer_headers):
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, make_user(db, "other@example.com"), product, unit, BookingStatus.CONFIRMED, 6, 8)

    response = checkout(client, customer_headers, product, pickup=5, days=3)

    assert response.status_code == 409
    assert "no longer available" in response.json()["detail"]


# ---------------------------------------------------------------- idempotency
def test_repeated_submission_returns_the_original_booking(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    make_unit(db, product, "CAM-002")

    first = checkout(client, customer_headers, product, key="checkout-attempt-1")
    second = checkout(client, customer_headers, product, key="checkout-attempt-1")

    assert (first.status_code, second.status_code) == (201, 200)
    assert first.json()["id"] == second.json()["id"]
    assert db.query(Booking).count() == 1 and db.query(Payment).count() == 1


def test_same_key_with_different_request_is_rejected(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    checkout(client, customer_headers, product, pickup=5, key="checkout-attempt-1")

    different_dates = checkout(client, customer_headers, product, pickup=20, key="checkout-attempt-1")

    assert different_dates.status_code == 422
    assert db.query(Booking).count() == 1


def test_idempotency_keys_are_per_customer(client, db, product):
    make_unit(db, product, "CAM-001")
    make_unit(db, product, "CAM-002")
    alice, bob = make_user(db, "alice@example.com"), make_user(db, "bob@example.com")

    a = checkout(client, auth_headers(alice), product, key="shared-key-value")
    b = checkout(client, auth_headers(bob), product, key="shared-key-value")

    assert (a.status_code, b.status_code) == (201, 201)
    assert a.json()["id"] != b.json()["id"]


def test_retry_after_failed_payment_with_same_key_can_succeed(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    failed = checkout(client, customer_headers, product, key="checkout-attempt-1", outcome="failure")
    retry = checkout(client, customer_headers, product, key="checkout-attempt-1", outcome="success")

    assert (failed.status_code, retry.status_code) == (402, 201)


# ---------------------------------------------------------------- concurrency
def test_simultaneous_checkouts_for_the_last_unit_book_it_once(db, product):
    make_unit(db, product, "CAM-001")
    users = [make_user(db, f"racer{i}@example.com") for i in range(4)]

    for round_number in range(3):  # a different date window each round, same single unit
        results: list[int] = []
        barrier = threading.Barrier(len(users))

        def attempt(user, pickup=5 + round_number * 10):
            client = TestClient(app)
            barrier.wait()
            results.append(checkout(client, auth_headers(user), product, pickup=pickup).status_code)

        threads = [threading.Thread(target=attempt, args=(user,)) for user in users]
        [thread.start() for thread in threads]
        [thread.join(30) for thread in threads]

        assert sorted(results) == [201, 409, 409, 409], f"round {round_number}: {results}"

    assert db.query(Booking).count() == 3


def test_checkout_waits_for_the_product_lock_then_rechecks_availability(db, product, customer, customer_headers):
    """Deterministic version of the race: hold the lock, let a checkout queue behind it,
    take the unit while holding the lock, and confirm the queued checkout sees that booking."""
    unit = make_unit(db, product, "CAM-001")
    rival = make_user(db, "rival@example.com")
    holder = SessionLocal()
    outcome = {}
    thread = threading.Thread(
        target=lambda: outcome.update(response=checkout(TestClient(app), customer_headers, product, pickup=5))
    )
    try:
        lock_product(holder, product.id)  # row lock held until holder commits
        thread.start()
        time.sleep(0.7)
        assert thread.is_alive(), "checkout should be blocked waiting for the product lock"

        make_booking(holder, rival, product, unit, BookingStatus.CONFIRMED, 5, 8)  # commits, releasing the lock
    finally:
        holder.rollback()  # never leave the lock held, even if an assertion failed
        holder.close()
        if thread.ident is not None:
            thread.join(15)

    assert outcome["response"].status_code == 409
    assert db.query(Booking).filter(Booking.user_id == customer.id).count() == 0


# ---------------------------------------------------------------- cancellation & refund
def test_customer_cancels_before_pickup_and_payment_is_refunded(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    booking_id = checkout(client, customer_headers, product).json()["id"]

    response = client.post(f"{API}/bookings/{booking_id}/cancel", json={"reason": "Plans changed"}, headers=customer_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CANCELLED" and body["payment_status"] == "REFUNDED"
    assert body["cancellation_reason"] == "Plans changed"
    assert db.query(Payment).one().status == PaymentStatus.REFUNDED
    assert quote(client, product).json()["available"] is True  # the unit is free again


def test_cancel_without_body_uses_default_reason(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    booking_id = checkout(client, customer_headers, product).json()["id"]
    response = client.post(f"{API}/bookings/{booking_id}/cancel", headers=customer_headers)
    assert response.json()["cancellation_reason"] == "Cancelled by customer"


def test_cancelling_twice_is_an_invalid_transition(client, db, product, customer_headers):
    make_unit(db, product, "CAM-001")
    booking_id = checkout(client, customer_headers, product).json()["id"]
    client.post(f"{API}/bookings/{booking_id}/cancel", headers=customer_headers)

    assert client.post(f"{API}/bookings/{booking_id}/cancel", headers=customer_headers).status_code == 400


def test_customer_cannot_cancel_on_or_after_pickup_day_but_admin_can(client, db, product, customer, admin_headers, customer_headers):
    unit = make_unit(db, product, "CAM-001")
    booking = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, pickup_offset=0, return_offset=2)

    by_customer = client.post(f"{API}/bookings/{booking.id}/cancel", headers=customer_headers)
    by_admin = client.post(f"{API}/admin/bookings/{booking.id}/cancel", headers=admin_headers)

    assert by_customer.status_code == 400
    assert by_admin.status_code == 200 and by_admin.json()["cancellation_reason"] == "Cancelled by administrator"


def test_customer_cannot_cancel_after_pickup_or_return(client, db, product, customer, customer_headers):
    unit = make_unit(db, product, "CAM-001")
    picked_up = make_booking(db, customer, product, unit, BookingStatus.PICKED_UP, -1, 2)
    returned = make_booking(db, customer, product, unit, BookingStatus.RETURNED, -10, -7)

    for booking in (picked_up, returned):
        assert client.post(f"{API}/bookings/{booking.id}/cancel", headers=customer_headers).status_code == 400


# ---------------------------------------------------------------- access control
def test_customers_see_only_their_own_bookings(client, db, product, customer, customer_headers):
    unit = make_unit(db, product, "CAM-001")
    mine = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 5, 8)
    stranger = make_user(db, "stranger@example.com")
    theirs = make_booking(db, stranger, product, unit, BookingStatus.CONFIRMED, 20, 22)

    listing = client.get(f"{API}/bookings", headers=customer_headers).json()

    assert [b["id"] for b in listing] == [mine.id]
    assert client.get(f"{API}/bookings/{mine.id}", headers=customer_headers).status_code == 200
    assert client.get(f"{API}/bookings/{theirs.id}", headers=customer_headers).status_code == 404
    assert client.post(f"{API}/bookings/{theirs.id}/cancel", headers=customer_headers).status_code == 404
    assert db.get(Booking, theirs.id).status == BookingStatus.CONFIRMED


def test_admin_booking_endpoints_reject_customers(client, db, product, customer, customer_headers):
    unit = make_unit(db, product, "CAM-001")
    booking = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 0, 2)

    for method, path in [
        ("get", "/admin/bookings"),
        ("get", f"/admin/bookings/{booking.id}"),
        ("post", f"/admin/bookings/{booking.id}/pickup"),
        ("post", f"/admin/bookings/{booking.id}/return"),
        ("post", f"/admin/bookings/{booking.id}/cancel"),
    ]:
        assert getattr(client, method)(API + path, headers=customer_headers).status_code == 403, path
        assert getattr(client, method)(API + path).status_code == 401, path


# ---------------------------------------------------------------- pickup & return
def test_admin_pickup_then_return_full_lifecycle(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    booking = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, pickup_offset=0, return_offset=2)

    picked = client.post(f"{API}/admin/bookings/{booking.id}/pickup", headers=admin_headers)
    returned = client.post(f"{API}/admin/bookings/{booking.id}/return", json={"condition": "FAIR"}, headers=admin_headers)

    assert picked.status_code == 200 and picked.json()["status"] == "PICKED_UP"
    assert picked.json()["actual_pickup_at"] is not None
    assert returned.status_code == 200 and returned.json()["status"] == "RETURNED"
    assert returned.json()["actual_return_at"] is not None
    db.refresh(unit)
    assert unit.condition == EquipmentCondition.FAIR


def test_return_without_body_keeps_unit_condition(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    booking = make_booking(db, customer, product, unit, BookingStatus.PICKED_UP, -1, 2)

    assert client.post(f"{API}/admin/bookings/{booking.id}/return", headers=admin_headers).status_code == 200
    db.refresh(unit)
    assert unit.condition == EquipmentCondition.EXCELLENT


def test_pickup_only_during_the_scheduled_period(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    too_early = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 3, 5)
    too_late = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, -5, -2)

    for booking in (too_early, too_late):
        assert client.post(f"{API}/admin/bookings/{booking.id}/pickup", headers=admin_headers).status_code == 400


def test_invalid_status_transitions_are_rejected(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    confirmed = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 0, 2)
    picked_up = make_booking(db, customer, product, unit, BookingStatus.PICKED_UP, -3, -1)
    returned = make_booking(db, customer, product, unit, BookingStatus.RETURNED, -9, -7)
    cancelled = make_booking(db, customer, product, unit, BookingStatus.CANCELLED, 10, 12)

    attempts = [
        (confirmed, "return"),  # CONFIRMED -> RETURNED is not allowed
        (picked_up, "pickup"),
        (picked_up, "cancel"),  # cannot cancel equipment that is out
        (returned, "pickup"),
        (returned, "return"),
        (returned, "cancel"),
        (cancelled, "pickup"),
        (cancelled, "return"),
    ]
    for booking, action in attempts:
        response = client.post(f"{API}/admin/bookings/{booking.id}/{action}", headers=admin_headers)
        assert response.status_code == 400, (booking.status, action)


def test_pickup_blocked_while_unit_is_still_out_with_previous_renter(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, customer, product, unit, BookingStatus.PICKED_UP, -6, -1)
    waiting = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 0, 2)

    assert client.post(f"{API}/admin/bookings/{waiting.id}/pickup", headers=admin_headers).status_code == 409


def test_return_cannot_mark_unit_damaged_while_future_bookings_depend_on_it(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    out = make_booking(db, customer, product, unit, BookingStatus.PICKED_UP, -1, 2)
    upcoming = make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 10, 12)

    blocked = client.post(f"{API}/admin/bookings/{out.id}/return", json={"condition": "DAMAGED"}, headers=admin_headers)
    assert blocked.status_code == 409 and upcoming.booking_reference in blocked.json()["detail"]
    assert db.get(Booking, out.id).status == BookingStatus.PICKED_UP

    client.post(f"{API}/admin/bookings/{upcoming.id}/cancel", headers=admin_headers)  # resolve it first
    done = client.post(f"{API}/admin/bookings/{out.id}/return", json={"condition": "DAMAGED"}, headers=admin_headers)
    assert done.status_code == 200


def test_admin_booking_list_filters_and_search(client, db, product, customer, admin_headers):
    unit = make_unit(db, product, "CAM-001")
    make_booking(db, customer, product, unit, BookingStatus.CONFIRMED, 5, 8)
    make_booking(db, customer, product, unit, BookingStatus.RETURNED, -10, -7)

    everything = client.get(f"{API}/admin/bookings", headers=admin_headers).json()
    returned = client.get(f"{API}/admin/bookings", params={"status_filter": "RETURNED"}, headers=admin_headers).json()
    by_name = client.get(f"{API}/admin/bookings", params={"search": "casey"}, headers=admin_headers).json()
    nobody = client.get(f"{API}/admin/bookings", params={"search": "zzz"}, headers=admin_headers).json()

    assert everything["total"] == 2 and everything["items"][0]["customer"]["full_name"] == "Casey Customer"
    assert returned["total"] == 1 and by_name["total"] == 2 and nobody["total"] == 0
