from __future__ import annotations

import ipaddress

from django.core.exceptions import ValidationError

from apps.internet.constants import BLOCKED_DOCUMENT_EXTENSIONS, DEFAULT_ALLOWED_DOCUMENT_EXTENSIONS


def validate_public_ip(value: str | None) -> None:
    if not value:
        return
    try:
        ipaddress.ip_address(value.strip())
    except ValueError as exc:
        raise ValidationError("Ingrese una dirección IPv4 o IPv6 válida.") from exc


def validate_upload_extension(filename: str, allowed: tuple[str, ...] | None = None) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in BLOCKED_DOCUMENT_EXTENSIONS:
        raise ValidationError("Tipo de archivo no permitido por seguridad.")
    allowed_set = set(allowed or DEFAULT_ALLOWED_DOCUMENT_EXTENSIONS)
    if ext not in allowed_set:
        raise ValidationError(
            f"Extensión no permitida. Use: {', '.join(sorted(allowed_set))}."
        )
