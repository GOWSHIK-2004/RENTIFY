import io
import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.product import Product

logger = logging.getLogger("rentify.images")

# Detected by Pillow from the file contents, never from the client's filename or content-type.
ALLOWED_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
PRODUCT_IMAGE_DIR = "products"


def _bad_request(message: str) -> HTTPException:
    return HTTPException(status.HTTP_400_BAD_REQUEST, message)


def _read_limited(upload: UploadFile, limit: int) -> bytes:
    data = upload.file.read(limit + 1)
    if len(data) > limit:
        raise _bad_request(f"Image is larger than {limit // (1024 * 1024)} MB.")
    return data


def _detect_extension(data: bytes) -> str:
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()  # parses the file; raises if it is not a real image
            image_format = image.format
    except Exception:
        raise _bad_request("File is not a valid image.")
    if image_format not in ALLOWED_FORMATS:
        raise _bad_request("Only JPEG, PNG and WebP images are allowed.")
    return ALLOWED_FORMATS[image_format]


def _delete_stored_file(image_path: str | None) -> None:
    if not image_path:
        return
    upload_root = get_settings().upload_dir.resolve()
    target = (upload_root / image_path).resolve()
    # Never delete anything outside the uploads directory.
    if upload_root in target.parents and target.is_file():
        target.unlink()


def save_product_image(db: Session, product: Product, upload: UploadFile) -> Product:
    settings = get_settings()
    data = _read_limited(upload, settings.max_upload_bytes)
    extension = _detect_extension(data)

    # The stored name is generated here; the client-supplied filename is ignored,
    # which also rules out directory traversal.
    filename = f"{uuid.uuid4().hex}{extension}"
    folder = Path(settings.upload_dir) / PRODUCT_IMAGE_DIR
    folder.mkdir(parents=True, exist_ok=True)
    (folder / filename).write_bytes(data)

    old_path = product.image_path
    new_path = f"{PRODUCT_IMAGE_DIR}/{filename}"
    product.image_path = new_path
    try:
        db.commit()
    except Exception:
        db.rollback()
        _delete_stored_file(new_path)  # do not leave an orphan file behind
        raise
    _delete_stored_file(old_path)
    logger.info("Stored image for product id=%s", product.id)
    return product
