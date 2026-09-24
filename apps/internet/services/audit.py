from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User

from apps.administration.services.audit import get_client_ip, log_audit_event
from apps.internet.constants import AUDIT_INTERNET_ACTION_LABELS


def log_internet_event(
    *,
    request,
    actor: User,
    action: str,
    record_type: str,
    record_id: int,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
) -> None:
    payload_old = {"module": "internet", "record_type": record_type, "record_id": record_id}
    payload_new = {"module": "internet", "record_type": record_type, "record_id": record_id}
    if old_values:
        payload_old.update(old_values)
    if new_values:
        payload_new.update(new_values)
    log_audit_event(
        actor=actor,
        action=action,
        old_values=payload_old,
        new_values=payload_new,
        ip_address=get_client_ip(request) if request else None,
    )


def internet_audit_label(action: str) -> str:
    return AUDIT_INTERNET_ACTION_LABELS.get(action, action)
