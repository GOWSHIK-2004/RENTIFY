# Rentify

**Rent More. Own Less.**

Rentify is an equipment rental web application: customers browse cameras, consoles, laptops, drones, instruments,
audio gear and projectors, pick dates, see a live price and availability, and book. An administrator prepares the
equipment, hands it over, and records its return. Everything runs on real FastAPI endpoints and PostgreSQL data.

> **Demonstration project.** Payments are simulated, no card details are collected, and nothing is delivered.
> It was built to practise full-stack development and to be read as a learning codebase.

## Problem statement

Buying expensive equipment you will use for a weekend is wasteful. A rental business needs to know, for a given
physical item and a given set of dates, whether it is free, charge a consistent price, and never promise the same
item to two people. Rentify models exactly that: **products** (a camera model), **inventory units** (the three
physical cameras of that model), and **bookings** that reserve one unit for a date range.

## Features

**Customers**
* Register, log in, edit profile
* Search by name or brand, filter by category and price, sort by price or newest, paginate (all in the database)
* Product page with specifications, reviews, date pickers, live availability and total
* Checkout with simulated payment (success or failure), safe against double clicks
* Booking history (upcoming, active, completed, cancelled), cancel before pickup with automatic simulated refund
* Review equipment after returning it; edit or delete your own reviews

**Administrators** (separate `/admin` area)
* Dashboard: live counts, revenue, monthly revenue chart, status chart, most rented equipment
* Manage products (create, edit, change price, upload image, feature, archive), categories (archive, never delete)
  and physical inventory units
* Process pickups and returns (with equipment condition), cancel bookings, see overdue rentals
* View customers and simulated payments

**Rules enforced by the backend**
* Prices are calculated server-side with `Decimal`; booking prices are snapshots
* Availability is calculated from bookings (`existing_pickup < new_return AND existing_return > new_pickup`)
* No double booking: a transaction with a row lock on the product re-checks availability at confirmation
* Idempotency keys make repeated checkout submissions safe
* All permissions are checked on the server; customers can only see their own bookings and reviews

## Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite 6, Tailwind CSS 4, React Router, Axios, Lucide icons, Recharts |
| Backend | Python, FastAPI, Uvicorn, Pydantic 2, SQLAlchemy 2 (sync), Alembic, Psycopg 3, PyJWT, Argon2 |
| Database | PostgreSQL 16 |
| Tests | Pytest, FastAPI `TestClient` |
| Local DB | Docker Compose, for the **database only** |

## Architecture

```
React (5173)  --JSON + Bearer JWT-->  FastAPI (8000)  --SQLAlchemy-->  PostgreSQL (5432)
 presentation                          routes / schemas / services       data + constraints
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Database ER diagram

```mermaid
erDiagram
    users ||--o{ bookings : makes
    users ||--o{ reviews : writes
    categories ||--o{ products : groups
    products ||--o{ inventory_units : "has units"
    products ||--o{ bookings : "rented in"
    products ||--o{ reviews : receives
    inventory_units ||--o{ bookings : "assigned to"
    bookings ||--o| payments : "paid by"
    bookings ||--o| reviews : "reviewed once"
```

Full diagram with columns, constraints, indexes and example SQL: [docs/DATABASE.md](docs/DATABASE.md).

## Repository structure

```
RENTIFY/
  docker-compose.yml          local PostgreSQL (+ a separate test database)
  README.md
  docs/
    ARCHITECTURE.md  DATABASE.md  CODEBASE_GUIDE.md
    Rentify - Dev Specs.pdf   the original specification
  backend/
    app/
      main.py config.py database.py dependencies.py
      models/    SQLAlchemy tables
      schemas/   Pydantic request/response models
      routes/    HTTP endpoints
      services/  business logic
      utils/     security, dates, text helpers
    alembic/     migrations
    tests/       pytest suite
    uploads/     uploaded product images (git-ignored)
    seed.py      demo data
    requirements.txt  .env.example
  frontend/
    src/
      api/ components/ contexts/ hooks/ layouts/ utils/
      pages/customer  pages/auth  pages/admin
    package.json  package-lock.json  vite.config.js
```

New to the code? Start with [docs/CODEBASE_GUIDE.md](docs/CODEBASE_GUIDE.md).

## Local installation

**Prerequisites:** Python 3.11+ (developed on 3.11; 3.12 also fine), Node.js 20+, and Docker (only to run PostgreSQL).
Commands below are for a Unix-style shell; on Windows PowerShell see the notes after each block.

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts PostgreSQL 16 on port 5432 with database `rentify` for the app and `rentify_test` for the tests
(user `rentify`, password `rentify_dev_password`: development only). Data persists in a Docker volume.

Prefer your own PostgreSQL? Create two databases yourself and put their URLs in `backend/.env` (next step).

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                 # Windows: Copy-Item .env.example .env
```

### 3. Environment configuration

Edit `backend/.env`:

| Variable | Meaning |
|---|---|
| `DATABASE_URL` | app database (`postgresql+psycopg://user:pass@host:5432/rentify`) |
| `TEST_DATABASE_URL` | database used by pytest; its name **must end in `_test`** |
| `JWT_SECRET` | random string of at least 32 characters (the app refuses to start otherwise). Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | token lifetime (default 60) |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | the administrator the seed script creates. The email must be a valid address (for example `admin@rentify.example.com`; `.local` and `.test` are rejected) |
| `FRONTEND_ORIGIN` | the only origin allowed by CORS (`http://localhost:5173`) |

Never commit `.env`; it is git-ignored.

### 4. Database migrations

```bash
alembic upgrade head
```

### 5. Seed demo data

```bash
python seed.py
```

Creates 7 categories, 20 products (placeholder images are generated locally), 40 inventory units, the
administrator, four customers, bookings in every state (including one overdue), payments and reviews. It is
**idempotent**: run it as often as you like, nothing is duplicated and existing data is never modified.

Demo accounts:

| Role | Login | Password |
|---|---|---|
| Admin | the `ADMIN_EMAIL` you set | the `ADMIN_PASSWORD` you set |
| Customer | `priya.sharma@example.com` (also `rahul.verma@`, `ananya.iyer@`, `karthik.nair@` `example.com`) | `Customer@123` |

### 6. Start the API

```bash
uvicorn app.main:app --reload
```

* API: http://localhost:8000
* Swagger UI: http://localhost:8000/docs

### 7. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. To point at a different API, copy `frontend/.env.example` to `frontend/.env` and
change `VITE_API_BASE_URL`.

## API documentation

Interactive documentation is generated by FastAPI at **http://localhost:8000/docs**. All endpoints are under
`/api/v1`. Errors are `{"detail": ...}`.

| Area | Endpoints | Access |
|---|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` | public / user |
| Profile | `GET`, `PATCH /users/me` | user |
| Categories | `GET /categories`; `POST`, `PATCH /{id}`, `DELETE /{id}` (archives) | public / admin |
| Products | `GET /products`, `/products/featured`, `/products/{id}`; `POST`, `PATCH /{id}`, `DELETE /{id}` (archives) | public / admin |
| Availability | `GET /products/{id}/availability`, `POST /bookings/quote` | public |
| Bookings | `POST /bookings`, `GET /bookings`, `GET /bookings/{id}`, `POST /bookings/{id}/cancel` | owner |
| Reviews | `GET /products/{id}/reviews`; `POST /reviews`, `PATCH`, `DELETE /reviews/{id}` | public / owner |
| Admin bookings | `GET /admin/bookings`, `GET /admin/bookings/{id}`, `POST .../pickup`, `.../return`, `.../cancel` | admin |
| Inventory | `GET`, `POST /admin/inventory`, `PATCH /admin/inventory/{id}` | admin |
| Admin data | `GET /admin/dashboard`, `/admin/users`, `/admin/payments`, `POST /admin/products/{id}/image` | admin |

Status codes: `200`/`201` success, `400` business rule, `401` not authenticated, `402` simulated payment failed,
`403` not allowed, `404` missing, `409` conflict (unavailable, duplicate, price changed), `422` invalid input,
`500` unexpected (details are logged, never returned).

## Running the tests

Start PostgreSQL first (`docker compose up -d`), then:

```bash
cd backend
pytest
```

89 tests cover authentication, products and search, inventory rules, image upload, rental dates and pricing,
availability and overlaps, checkout (success, failed payment, price change, idempotency), concurrent booking
attempts, cancellation and refund, pickup/return and invalid transitions, access control, reviews, and the admin
dashboard.

The tests run against `TEST_DATABASE_URL` only. `tests/conftest.py` refuses to start unless its database name
ends in `_test`, and the schema is built from the real Alembic migrations.

Frontend build check:

```bash
cd frontend
npm run build
```

## Known limitations

* **Login is lost on refresh.** For this MVP the JWT lives only in memory (not `localStorage`), so refreshing
  the browser requires logging in again. A production app would use an HttpOnly refresh cookie.
* **Payments are simulated.** There is no gateway, no card data, and refunds are just a status change.
* **One product per booking, no cart.** Each booking reserves a single unit.
* **No taxes, deposits, coupons, delivery or dynamic pricing.**
* **Specification order is not preserved.** Specifications are stored as PostgreSQL `JSONB`, which orders keys
  itself, so they may display in a different order than entered.
* **Admin product/inventory pickers load up to 50 products per request** (they page through all of them).
* **Images are stored on local disk** (`backend/uploads`), served by FastAPI. No CDN or object storage.
* **No email notifications, no password reset, no rate limiting.**
* **Docker is used only for the local database.** The API and frontend run directly on your machine; there is no
  containerised deployment.
* **Python version:** the spec calls for Python 3.12; the project was developed and tested on 3.11.9 and uses no
  3.12-only features.
* **Not browser-tested on a phone.** The layout is responsive, but the automated browser run used a desktop viewport.

## License

Educational demonstration project.
