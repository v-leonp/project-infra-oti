from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model

from apps.administration.services.audit import get_client_ip, log_audit_event
from apps.catalogs.constants import (
    AUDIT_CATALOG_ACTIVATED,
    AUDIT_CATALOG_CREATED,
    AUDIT_CATALOG_DEACTIVATED,
    AUDIT_CATALOG_RELATIONS_UPDATED,
    AUDIT_CATALOG_UPDATED,
)
from apps.catalogs.utils import normalize_code, normalize_name


class CatalogServiceError(ValidationError):
    pass


def _snapshot(instance: Model, catalog_key: str, extra: dict | None = None) -> dict[str, Any]:
    data = {
        "catalog": catalog_key,
        "record_id": instance.pk,
        "code": getattr(instance, "code", ""),
        "is_active": getattr(instance, "is_active", None),
    }
    for field in ("name", "legal_name", "ruc", "first_name", "last_name"):
        if hasattr(instance, field):
            data[field] = getattr(instance, field)
    if extra:
        data.update(extra)
    return data


def _ensure_unique_code(model, code: str, exclude_pk: int | None = None) -> None:
    normalized = normalize_code(code)
    qs = model.objects.filter(code__iexact=normalized)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise CatalogServiceError({"code": "Este código ya está registrado."})


def _ensure_unique_name(model, name: str, exclude_pk: int | None = None) -> None:
    normalized = normalize_name(name)
    if not hasattr(model, "name"):
        return
    qs = model.objects.filter(name__iexact=normalized)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise CatalogServiceError({"name": "Este nombre ya está registrado."})


@transaction.atomic
def create_catalog_record(
    *,
    model,
    catalog_key: str,
    actor,
    request,
    code: str,
    fields: dict[str, Any],
    m2m: dict[str, list] | None = None,
) -> Model:
    _ensure_unique_code(model, code)
    if "name" in fields:
        _ensure_unique_name(model, fields["name"])
    instance = model(
        code=normalize_code(code),
        created_by=actor,
        updated_by=actor,
        **fields,
    )
    instance.full_clean()
    instance.save()
    if m2m:
        for field_name, values in m2m.items():
            getattr(instance, field_name).set(values)
    log_audit_event(
        actor=actor,
        action=AUDIT_CATALOG_CREATED,
        old_values={},
        new_values=_snapshot(instance, catalog_key),
        ip_address=get_client_ip(request),
    )
    return instance


@transaction.atomic
def update_catalog_record(
    *,
    instance: Model,
    catalog_key: str,
    actor,
    request,
    code: str,
    fields: dict[str, Any],
    m2m: dict[str, list] | None = None,
) -> Model:
    old = _snapshot(instance, catalog_key)
    _ensure_unique_code(instance.__class__, code, exclude_pk=instance.pk)
    if "name" in fields:
        _ensure_unique_name(instance.__class__, fields["name"], exclude_pk=instance.pk)
    instance.code = normalize_code(code)
    for key, value in fields.items():
        setattr(instance, key, value)
    instance.updated_by = actor
    instance.full_clean()
    instance.save()
    if m2m:
        for field_name, values in m2m.items():
            old_rel = list(getattr(instance, field_name).values_list("pk", flat=True))
            getattr(instance, field_name).set(values)
            log_audit_event(
                actor=actor,
                action=AUDIT_CATALOG_RELATIONS_UPDATED,
                old_values={"catalog": catalog_key, "record_id": instance.pk, field_name: old_rel},
                new_values={"catalog": catalog_key, "record_id": instance.pk, field_name: values},
                ip_address=get_client_ip(request),
            )
    log_audit_event(
        actor=actor,
        action=AUDIT_CATALOG_UPDATED,
        old_values=old,
        new_values=_snapshot(instance, catalog_key),
        ip_address=get_client_ip(request),
    )
    return instance


def validate_deactivate(instance: Model, catalog_key: str) -> None:
    from apps.catalogs.models import Provider, Responsible, ServiceType, Site

    if isinstance(instance, ServiceType):
        if Provider.objects.filter(service_types=instance, is_active=True).exists():
            raise CatalogServiceError(
                "No puede desactivar este tipo de servicio: está asociado a proveedores activos."
            )
    if isinstance(instance, Site):
        if Responsible.objects.filter(site=instance, is_active=True).exists():
            raise CatalogServiceError(
                "No puede desactivar esta sede: tiene responsables activos asociados."
            )


@transaction.atomic
def set_catalog_active_state(
    *,
    instance: Model,
    catalog_key: str,
    actor,
    request,
    activate: bool,
) -> Model:
    if not activate:
        validate_deactivate(instance, catalog_key)
    old_active = instance.is_active
    instance.is_active = activate
    instance.updated_by = actor
    instance.save(update_fields=["is_active", "updated_at", "updated_by"])
    action = AUDIT_CATALOG_ACTIVATED if activate else AUDIT_CATALOG_DEACTIVATED
    log_audit_event(
        actor=actor,
        action=action,
        old_values=_snapshot(instance, catalog_key, {"is_active": old_active}),
        new_values=_snapshot(instance, catalog_key, {"is_active": activate}),
        ip_address=get_client_ip(request),
    )
    return instance
