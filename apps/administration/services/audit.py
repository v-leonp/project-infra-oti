from __future__ import annotations

from typing import Any

from django.contrib.auth.models import Group, User

from apps.administration.models import AuditLog

SENSITIVE_KEYS = frozenset(
    {"password", "password1", "password2", "token", "secret", "csrf", "session", "cookie"}
)


def _sanitize_payload(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    return {key: value for key, value in data.items() if key.lower() not in SENSITIVE_KEYS}


def user_snapshot(user: User) -> dict[str, Any]:
    return {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": user.is_active,
        "role": user.groups.first().name if user.groups.exists() else None,
    }


def log_audit_event(
    *,
    actor: User,
    action: str,
    target_user: User | None = None,
    target_group: Group | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    return AuditLog.objects.create(
        actor=actor,
        target_user=target_user,
        target_group=target_group,
        action=action,
        old_values=_sanitize_payload(old_values),
        new_values=_sanitize_payload(new_values),
        ip_address=ip_address,
    )


def get_client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
