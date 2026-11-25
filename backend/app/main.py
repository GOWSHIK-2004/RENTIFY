import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.routes import admin, auth, bookings, categories, inventory, products, users

API_PREFIX = "/api/v1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("rentify")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Rentify API", description="Rent More. Own Less.", version="1.0.0")

    # Only the local React dev origin may call the API from a browser.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    for router in (
        auth.router,
        users.router,
        categories.router,
        products.router,
        bookings.router,
        inventory.router,
        admin.router,
    ):
        app.include_router(router, prefix=API_PREFIX)

    # Product images are served straight from the uploads directory.
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

    @app.get(f"{API_PREFIX}/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def register_error_handlers(app: FastAPI) -> None:
    """Every error response uses {"detail": ...}; internals are logged, never returned."""

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "A database error occurred."})

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Something went wrong."})


app = create_app()
