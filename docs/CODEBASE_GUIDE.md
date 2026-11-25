# Codebase guide

A walkthrough of the backend for someone reading it for the first time. All paths are relative to `backend/`.
For the big picture read [ARCHITECTURE.md](ARCHITECTURE.md) first; for tables and SQL read
[DATABASE.md](DATABASE.md).

## Where to start

Read these in order. Together they are about 1,000 lines and cover most of the interesting logic.

| # | File | Why |
|---|---|---|
| 1 | `app/main.py` | how the app is assembled: routers, CORS, error handlers |
| 2 | `app/models/booking.py` | the central table and its constraints |
| 3 | `app/dependencies.py` | how authentication and admin checks are reused |
| 4 | `app/services/pricing_service.py` | the date and price rules (small and pure) |
| 5 | `app/services/booking_service.py` | availability, checkout transaction, status changes |
| 6 | `tests/test_bookings.py` | the rules written as examples |

Request path for every endpoint: **route → (schema validates) → service → model → database → schema → JSON**.

## Important files

| File | What it does |
|---|---|
| `app/config.py` | `Settings` read from environment / `.env` (`get_settings()`) |
| `app/database.py` | `engine`, `SessionLocal`, `Base`, and `get_db()` (one session per request) |
| `app/utils/security.py` | Argon2 hashing and JWT create/decode |
| `app/utils/dates.py` | `business_today()` in `Asia/Kolkata` |
| `app/services/product_service.py` | catalog queries and `lock_product()` |
| `app/services/inventory_service.py` | which units are usable; `unresolved_bookings()` |
| `app/services/image_service.py` | image validation and storage |
| `seed.py` | idempotent demo data |
| `tests/conftest.py` | test database setup (built with the real migrations) |
| `tests/factories.py` | `make_user`, `make_product`, `make_booking`, ... |

## 1. User registration

`POST /api/v1/auth/register`

1. `app/routes/auth.py: register` receives the body. FastAPI validates it against
   `app/schemas/user.py: RegisterRequest` first: email format, password at least 8 characters, passwords match.
   The email is lower-cased and trimmed by a validator. Bad input never reaches the service (`422`).
2. `app/services/auth_service.py: register_customer`:
   * rejects an existing email with `409`;
   * hashes the password with `utils/security.py: hash_password` (Argon2);
   * creates the `User` with `role=CUSTOMER`. The role is hard-coded here; it is not a request field;
   * commits. If two registrations race, the unique index on `users.email` raises `IntegrityError`, which is
     turned into the same `409`.
3. The route returns `UserResponse` (no password hash). The frontend then logs the user in
   (`AuthContext.register`).

## 2. User login

`POST /api/v1/auth/login`

1. `routes/auth.py: login` calls `auth_service.authenticate`.
2. `authenticate` loads the user by email and calls `utils/security.py: verify_password`. Unknown email and wrong
   password produce the same `401 "Incorrect email or password."`.
3. `utils/security.py: create_access_token(user_id, role)` signs a JWT with `sub` and an `exp` from
   `ACCESS_TOKEN_EXPIRE_MINUTES`.
4. The response is `{access_token, token_type, user}`. React keeps the token in memory (`frontend/src/api/client.js`).

Later requests send `Authorization: Bearer ...`. `app/dependencies.py: get_current_user` decodes the token with
`decode_access_token` (checks signature, expiry, algorithm), loads the user, and returns it. Any failure is `401`.
`require_admin` builds on it and answers `403` for non-admins. `ensure_owner` hides other people's data behind
`404`. Routes opt in simply by declaring `Depends(get_current_user)` or `Depends(require_admin)`.

## 3. Product retrieval

`GET /api/v1/products?q=sony&category=cameras&min_price=500&sort=price_asc&page=1`

1. `app/routes/products.py: list_products` declares each query parameter with validation (`sort` is a `Literal`,
   `page_size` is capped at 50) and packs them into a `ProductFilters` dataclass.
2. `app/services/product_service.py: list_products` builds the SQL with SQLAlchemy:
   * `_products_query()` selects the product, joins its category, and left-joins a subquery of average rating and
     review count, so ratings arrive in the same query (no N+1).
   * conditions are added for search (`ILIKE` on name or brand, with `%` and `_` escaped by
     `utils/text.py: escape_like`), category slug, and price range;
   * inactive products and products in archived categories are excluded unless an administrator asked for
     `include_inactive` (guarded by `dependencies.py: allow_inactive`);
   * `SORT_ORDERS` maps `newest`, `price_asc`, `price_desc` to `ORDER BY` clauses, each with an `id` tie-breaker so
     pages are stable;
   * `LIMIT`/`OFFSET` implement pagination, and a count query provides `total` and `pages`.
3. `_to_response` converts rows to `ProductResponse`. Filtering happens in PostgreSQL, never in the browser.

A single product (`routes/products.py: get_product`) uses the same query. Inactive products return `404` to
customers but are visible to administrators.

## 4. Availability checking

`GET /api/v1/products/{id}/availability?pickup_date=...&return_date=...` (and `POST /bookings/quote`)

* Routes: `routes/products.py: check_availability` and `routes/bookings.py: quote`, both calling
  `app/services/booking_service.py: build_quote`.
* `build_quote` first calls `pricing_service.validate_rental_dates` (section 5), loads the product with
  `get_bookable_product` (`404` if inactive), then counts available units.
* The heart is `booking_service.py: _available_unit_conditions`. A unit qualifies when it belongs to the product,
  is `ACTIVE`, is not `DAMAGED`, is **not** in the set of units with an overlapping `CONFIRMED`/`PICKED_UP`
  booking (`pickup_date < requested_return AND return_date > requested_pickup`), and is **not** a unit that is
  still out past its return date.
* Nothing is reserved. There is no `available` column; availability only ever comes from `bookings`.

## 5. Rental price calculation

`app/services/pricing_service.py`:

* `validate_rental_dates(pickup, return)`: not in the past (Asia/Kolkata), return after pickup, between 1 and 30
  days. Returns the number of days or raises `400`.
* `rental_days(pickup, return)`: `(return_date - pickup_date).days`. The return day is not charged
  (Dec 1 to Dec 4 is 3 days).
* `calculate_total(daily_price, days)`: `Decimal` multiplication rounded to 2 places. `899 × 3 = 2697.00`.

This is the only place prices are computed. The quote endpoint and the checkout both call it, so the number the
customer sees and the number charged cannot drift apart in code.

## 6. Booking confirmation (checkout)

`POST /api/v1/bookings` → `routes/bookings.py: create_booking` → `services/booking_service.py: create_booking`

The body is `schemas/booking.py: BookingCreate`: product, dates, `expected_total`, `idempotency_key`, and the
simulated `payment_outcome`. In order:

1. Validate the dates (`validate_rental_dates`).
2. `product_service.lock_product`: `SELECT ... FOR UPDATE` on the product row. From here to the commit, other
   checkouts of this product wait.
3. **Idempotency**: look for an earlier booking by `(user_id, idempotency_key)`. Same fingerprint (product plus
   dates) → return the original booking with `200`. Different fingerprint → `422`.
4. A failed simulated payment → roll back, `402`. Nothing was created or reserved.
5. Pick the first free unit with the same availability conditions as section 4, ordered by asset code. None →
   `409 "no longer available"`.
6. Recalculate the total. If it differs from `expected_total` → `409` with `code: PRICE_CHANGED` and the new
   amounts; the frontend asks the customer to confirm again.
7. Create the `Booking` (copying `daily_price` and `total_amount` onto it) and its `Payment`, then one
   `db.commit()`. The booking, the allocated unit and the payment appear together or not at all.

`_abort()` rolls back before raising, which also releases the lock quickly. The database backs the code up: the
composite foreign key, check constraints and `uq_bookings_user_idempotency_key` would reject bad data even if
the Python had a bug.

## 7. Booking cancellation

`POST /api/v1/bookings/{id}/cancel` (customer) or `POST /api/v1/admin/bookings/{id}/cancel` (admin) →
`booking_service.py: cancel_booking(..., as_admin)`

1. `_lock_booking` locks the booking row, so a cancel and a pickup cannot both succeed.
2. A customer must own the booking (otherwise `404`).
3. `_check_transition` consults `ALLOWED_TRANSITIONS`: only `CONFIRMED → CANCELLED` is allowed; anything else is
   `400`.
4. A customer may cancel only before the pickup date; an admin may cancel any confirmed booking.
5. Set `status=CANCELLED`, store the reason, and set `payment.status = REFUNDED`, all in one commit.
   The unit is free again immediately because cancelled bookings never block availability.

## 8. Administrator pickup and return

`POST /api/v1/admin/bookings/{id}/pickup` and `/return` → `routes/admin.py` (router-level `require_admin`).

**Pickup**, `booking_service.py: pickup_booking`:

* lock the booking, check `CONFIRMED → PICKED_UP`;
* only during the rental period (`pickup_date <= today < return_date`);
* the unit must be in service, and must not still be out with a previous renter (`409`);
* set `status=PICKED_UP` and `actual_pickup_at` (UTC).

**Return**, `booking_service.py: return_booking`:

* lock the booking, check `PICKED_UP → RETURNED`;
* optionally record the unit's condition. If that makes the unit unusable (for example `DAMAGED`) while future
  confirmed bookings depend on it, the request is refused with `409` and lists them
  (`inventory_service.unresolved_bookings`): the admin resolves those first. The product lock is taken so no
  booking is assigned meanwhile;
* set `status=RETURNED` and `actual_return_at`.

**Overdue** is computed, not stored: `PICKED_UP` and `return_date < today`. It appears in
`booking_service.to_response` (`is_overdue`, `affected_by_overdue`), in the admin bookings filter, and in the
dashboard count.

## Conventions worth knowing

* Services raise `HTTPException`; routes stay thin.
* Money is `Decimal` in Python and `NUMERIC(10,2)` in the database; JSON carries it as a string.
* Business date = `business_today()`; timestamps = UTC.
* `with_for_update()` appears only in `lock_product` and `_lock_booking`: look there to see every lock.
* Tests run against `rentify_test` only (`tests/conftest.py` refuses any database name not ending in `_test`) and
  build the schema from the real Alembic migrations.
