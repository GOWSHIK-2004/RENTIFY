from app.models import BookingStatus, Review
from tests.factories import auth_headers, make_booking, make_unit, make_user

API = "/api/v1"


def returned_booking(db, user, product):
    unit = make_unit(db, product, f"CAM-{product.id}-{user.id}")
    return make_booking(db, user, product, unit, BookingStatus.RETURNED, -10, -7)


def post_review(client, headers, booking, rating=5, comment="Great camera"):
    return client.post(
        f"{API}/reviews", headers=headers, json={"booking_id": booking.id, "rating": rating, "comment": comment}
    )


def test_review_after_returned_rental(client, db, product, customer, customer_headers):
    booking = returned_booking(db, customer, product)

    response = post_review(client, customer_headers, booking)

    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 5 and body["product_id"] == product.id and body["booking_id"] == booking.id
    assert body["reviewer_name"] == "Casey C."  # public name hides the full surname


def test_review_without_completed_rental_is_rejected(client, db, product, customer, customer_headers):
    unit = make_unit(db, product, "CAM-001")
    for index, status in enumerate((BookingStatus.CONFIRMED, BookingStatus.PICKED_UP, BookingStatus.CANCELLED)):
        booking = make_booking(db, customer, product, unit, status, 20 + index * 5, 22 + index * 5)
        assert post_review(client, customer_headers, booking).status_code == 400
    assert db.query(Review).count() == 0


def test_invalid_rating_is_rejected(client, db, product, customer, customer_headers):
    booking = returned_booking(db, customer, product)
    for rating in (0, 6, -1):
        assert post_review(client, customer_headers, booking, rating=rating).status_code == 422


def test_one_review_per_booking(client, db, product, customer, customer_headers):
    booking = returned_booking(db, customer, product)
    assert post_review(client, customer_headers, booking).status_code == 201

    assert post_review(client, customer_headers, booking, rating=1).status_code == 409
    assert db.query(Review).count() == 1


def test_cannot_review_someone_elses_booking(client, db, product, customer_headers):
    stranger = make_user(db, "stranger@example.com")
    booking = returned_booking(db, stranger, product)

    assert post_review(client, customer_headers, booking).status_code == 404


def test_review_requires_login(client, db, product, customer):
    booking = returned_booking(db, customer, product)
    assert post_review(client, {}, booking).status_code == 401


def test_edit_and_delete_own_review(client, db, product, customer, customer_headers):
    review_id = post_review(client, customer_headers, returned_booking(db, customer, product)).json()["id"]

    edited = client.patch(f"{API}/reviews/{review_id}", json={"rating": 3, "comment": "Fine"}, headers=customer_headers)
    deleted = client.delete(f"{API}/reviews/{review_id}", headers=customer_headers)

    assert edited.status_code == 200 and edited.json()["rating"] == 3 and edited.json()["comment"] == "Fine"
    assert deleted.status_code == 204
    assert db.query(Review).count() == 0


def test_cannot_edit_or_delete_another_customers_review(client, db, product, customer, customer_headers):
    review_id = post_review(client, customer_headers, returned_booking(db, customer, product)).json()["id"]
    intruder = auth_headers(make_user(db, "intruder@example.com"))

    assert client.patch(f"{API}/reviews/{review_id}", json={"rating": 1}, headers=intruder).status_code == 404
    assert client.delete(f"{API}/reviews/{review_id}", headers=intruder).status_code == 404
    assert db.query(Review).one().rating == 5


def test_product_reviews_and_average_rating(client, db, product):
    for index, rating in enumerate((5, 4, 4)):
        reviewer = make_user(db, f"reviewer{index}@example.com", name=f"Rita Reviewer{index}")
        booking = returned_booking(db, reviewer, product)
        post_review(client, auth_headers(reviewer), booking, rating=rating)

    reviews = client.get(f"{API}/products/{product.id}/reviews").json()
    detail = client.get(f"{API}/products/{product.id}").json()
    listing = client.get(f"{API}/products").json()["items"][0]

    assert [r["rating"] for r in reviews] == [4, 4, 5]  # newest first
    assert detail["average_rating"] == 4.3 and detail["review_count"] == 3
    assert listing["average_rating"] == 4.3
    assert client.get(f"{API}/products/9999/reviews").status_code == 404
