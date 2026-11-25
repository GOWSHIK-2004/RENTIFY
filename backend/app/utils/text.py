import re


def slugify(value: str) -> str:
    """'Cameras & Photography' -> 'cameras-photography'."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "category"


def escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input is matched literally (use with escape='\\\\')."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
