from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import get_settings


def business_today() -> date:
    """Today's date in the business timezone (Asia/Kolkata), not the server's local zone."""
    return datetime.now(ZoneInfo(get_settings().business_timezone)).date()
