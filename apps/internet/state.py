from __future__ import annotations

from datetime import date

from django.conf import settings
from django.utils import timezone

from apps.internet.constants import (
    SERVICE_STATUS_ACTIVE,
    SERVICE_STATUS_EXPIRED,
    SERVICE_STATUS_EXPIRING,
    SERVICE_STATUS_INACTIVE,
    SERVICE_STATUS_OBSERVATIONS,
)


def expiry_warning_days() -> int:
    return int(getattr(settings, "INTERNET_SERVICE_EXPIRY_WARNING_DAYS", 30))


def compute_service_status(
    *,
    is_active: bool,
    end_date: date,
    marked_with_observations: bool,
    on_date: date | None = None,
) -> str:
    if not is_active:
        return SERVICE_STATUS_INACTIVE
    if marked_with_observations:
        return SERVICE_STATUS_OBSERVATIONS
    today = on_date or timezone.localdate()
    if end_date < today:
        return SERVICE_STATUS_EXPIRED
    days_left = (end_date - today).days
    if days_left <= expiry_warning_days():
        return SERVICE_STATUS_EXPIRING
    return SERVICE_STATUS_ACTIVE
