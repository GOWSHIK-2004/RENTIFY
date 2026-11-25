from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings
from app.models import User, UserRole
from tests.factories import PASSWORD

REGISTER = {
    "full_name": "Priya Sharma",
    "email": "  Priya@Example.COM ",
    "password": "s3cret-pass",
    "confirm_password": "s3cret-pass",
}


def test_register_success_normalizes_email_and_hashes_password(client, db):
    response = client.post("/api/v1/auth/register", json=REGISTER)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "priya@example.com"
    assert body["role"] == "CUSTOMER"
    assert "password" not in body and "password_hash" not in body

    stored = db.query(User).one()
    assert stored.password_hash.startswith("$argon2")


def test_register_cannot_choose_admin_role(client, db):
    client.post("/api/v1/auth/register", json={**REGISTER, "role": "ADMIN"})
    assert db.query(User).one().role == UserRole.CUSTOMER


def test_register_duplicate_email_conflicts(client):
    assert client.post("/api/v1/auth/register", json=REGISTER).status_code == 201
    duplicate = {**REGISTER, "email": "PRIYA@example.com"}
    assert client.post("/api/v1/auth/register", json=duplicate).status_code == 409


def test_register_validation_errors(client):
    short = {**REGISTER, "password": "short", "confirm_password": "short"}
    mismatch = {**REGISTER, "confirm_password": "different-pass"}
    bad_email = {**REGISTER, "email": "not-an-email"}
    for payload in (short, mismatch, bad_email):
        assert client.post("/api/v1/auth/register", json=payload).status_code == 422


def test_login_success_returns_token_and_user(client, customer):
    response = client.post("/api/v1/auth/login", json={"email": "Customer@Example.com", "password": PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "customer@example.com"
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200


def test_login_wrong_password_and_unknown_email_look_identical(client, customer):
    wrong_password = client.post("/api/v1/auth/login", json={"email": customer.email, "password": "nope-nope-nope"})
    unknown_email = client.post("/api/v1/auth/login", json={"email": "ghost@example.com", "password": PASSWORD})

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_requires_a_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_invalid_token_is_rejected(client):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_token_signed_with_wrong_secret_is_rejected(client, customer):
    forged = jwt.encode({"sub": str(customer.id), "exp": datetime.now(UTC) + timedelta(hours=1)}, "wrong-secret", "HS256")
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_expired_token_is_rejected(client, customer):
    settings = get_settings()
    expired = jwt.encode(
        {"sub": str(customer.id), "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret,
        settings.jwt_algorithm,
    )
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_update_profile(client, customer_headers):
    response = client.patch("/api/v1/users/me", json={"full_name": "  New Name "}, headers=customer_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"
