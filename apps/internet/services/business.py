from __future__ import annotations

from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from apps.catalogs.models import Provider, Site
from apps.internet.constants import (
    AUDIT_CONTRACT_CREATED,
    AUDIT_CONTRACT_UPDATED,
    AUDIT_DELIVERABLE_CREATED,
    AUDIT_DELIVERABLE_STATE,
    AUDIT_DELIVERABLE_UPDATED,
    AUDIT_DOCUMENT_UPLOADED,
    AUDIT_INCIDENT_CLOSED,
    AUDIT_INCIDENT_CREATED,
    AUDIT_INCIDENT_UPDATED,
    AUDIT_SERVICE_CREATED,
    AUDIT_SERVICE_DATES_CHANGED,
    AUDIT_SERVICE_PROVIDER_CHANGED,
    AUDIT_SERVICE_STATE_CHANGED,
    AUDIT_SERVICE_UPDATED,
    DELIVERABLE_STATUS_LATE,
    INCIDENT_STATUS_CLOSED,
    INCIDENT_STATUS_OPEN,
)
from apps.internet.models import (
    InternetService,
    InternetServiceStatusHistory,
    ServiceContract,
    ServiceDeliverable,
    ServiceDocument,
    ServiceIncident,
)
from apps.internet.selectors import service_snapshot
from apps.internet.services.audit import log_internet_event
from apps.internet.validators import validate_upload_extension


def _ensure_active_catalog(instance, label: str) -> None:
    if instance and hasattr(instance, "is_active") and not instance.is_active:
        raise ValidationError(f"El {label} seleccionado no está activo.")


def _normalize_code(code: str) -> str:
    return code.strip().upper()


@transaction.atomic
def create_service(request, user, data: dict) -> InternetService:
    code = _normalize_code(data["code"])
    if InternetService.objects.filter(code__iexact=code).exists():
        raise ValidationError("Ya existe un servicio con este código.")
    site = data["site"]
    provider = data["provider"]
    responsible = data.get("responsible")
    _ensure_active_catalog(site, "sede")
    _ensure_active_catalog(provider, "proveedor")
    if responsible:
        _ensure_active_catalog(responsible, "responsable")
    _check_duplicate_service(
        site=site,
        provider=provider,
        link_type=data["link_type"],
        circuit_id=data.get("circuit_id", ""),
        exclude_pk=None,
    )
    service = InternetService.objects.create(
        code=code,
        ods=data.get("ods"),
        oes=data.get("oes"),
        site=site,
        provider=provider,
        responsible=responsible,
        link_type=data["link_type"],
        contracted_speed=data["contracted_speed"],
        speed_unit=data.get("speed_unit") or "Mbps",
        public_ip=data.get("public_ip") or None,
        circuit_id=(data.get("circuit_id") or "").strip(),
        connection_medium=(data.get("connection_medium") or "").strip(),
        technical_observations=(data.get("technical_observations") or "").strip(),
        start_date=data["start_date"],
        end_date=data["end_date"],
        observations=(data.get("observations") or "").strip(),
        marked_with_observations=bool(data.get("marked_with_observations")),
        is_active=bool(data.get("is_active", True)),
        created_by=user,
        updated_by=user,
    )
    service.full_clean()
    status = service.display_status
    InternetServiceStatusHistory.objects.create(
        service=service,
        previous_status="",
        new_status=status,
        reason="Creación",
        changed_by=user,
        ip_address=_ip(request),
    )
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_SERVICE_CREATED,
        record_type="service",
        record_id=service.pk,
        new_values=service_snapshot(service),
    )
    return service


def _check_duplicate_service(
    *,
    site: Site,
    provider: Provider,
    link_type: str,
    circuit_id: str,
    exclude_pk: int | None,
) -> None:
    qs = InternetService.objects.filter(
        site=site,
        provider=provider,
        link_type=link_type,
        is_active=True,
    )
    if circuit_id:
        qs = qs.filter(circuit_id__iexact=circuit_id.strip())
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError("Ya existe un servicio activo con la misma sede, proveedor y enlace.")


@transaction.atomic
def update_service(request, user, service: InternetService, data: dict) -> InternetService:
    old = service_snapshot(service)
    old_provider = service.provider_id
    old_dates = (service.start_date, service.end_date)
    code = _normalize_code(data["code"])
    if InternetService.objects.filter(code__iexact=code).exclude(pk=service.pk).exists():
        raise ValidationError("Ya existe un servicio con este código.")
    site = data["site"]
    provider = data["provider"]
    responsible = data.get("responsible")
    _ensure_active_catalog(site, "sede")
    _ensure_active_catalog(provider, "proveedor")
    if responsible:
        _ensure_active_catalog(responsible, "responsable")
    _check_duplicate_service(
        site=site,
        provider=provider,
        link_type=data["link_type"],
        circuit_id=data.get("circuit_id", ""),
        exclude_pk=service.pk,
    )
    prev_status = service.display_status
    service.code = code
    service.ods = data.get("ods")
    service.oes = data.get("oes")
    service.site = site
    service.provider = provider
    service.responsible = responsible
    service.link_type = data["link_type"]
    service.contracted_speed = data["contracted_speed"]
    service.speed_unit = data.get("speed_unit") or "Mbps"
    service.public_ip = data.get("public_ip") or None
    service.circuit_id = (data.get("circuit_id") or "").strip()
    service.connection_medium = (data.get("connection_medium") or "").strip()
    service.technical_observations = (data.get("technical_observations") or "").strip()
    service.start_date = data["start_date"]
    service.end_date = data["end_date"]
    service.observations = (data.get("observations") or "").strip()
    service.marked_with_observations = bool(data.get("marked_with_observations"))
    service.is_active = bool(data.get("is_active", service.is_active))
    service.updated_by = user
    service.full_clean()
    service.save()
    new_status = service.display_status
    if prev_status != new_status:
        record_service_status_change(
            request, user, service, prev_status, new_status, reason="Actualización"
        )
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_SERVICE_UPDATED,
        record_type="service",
        record_id=service.pk,
        old_values=old,
        new_values=service_snapshot(service),
    )
    if old_provider != service.provider_id:
        log_internet_event(
            request=request,
            actor=user,
            action=AUDIT_SERVICE_PROVIDER_CHANGED,
            record_type="service",
            record_id=service.pk,
            old_values={"provider": old_provider},
            new_values={"provider": service.provider_id},
        )
    if old_dates != (service.start_date, service.end_date):
        log_internet_event(
            request=request,
            actor=user,
            action=AUDIT_SERVICE_DATES_CHANGED,
            record_type="service",
            record_id=service.pk,
            old_values={"start": str(old_dates[0]), "end": str(old_dates[1])},
            new_values={"start": str(service.start_date), "end": str(service.end_date)},
        )
    return service


@transaction.atomic
def update_service_state(
    request,
    user,
    service: InternetService,
    *,
    is_active: bool | None = None,
    marked_with_observations: bool | None = None,
    reason: str = "",
) -> InternetService:
    prev_status = service.display_status
    if is_active is not None:
        service.is_active = is_active
    if marked_with_observations is not None:
        service.marked_with_observations = marked_with_observations
    service.updated_by = user
    service.save()
    new_status = service.display_status
    if prev_status != new_status:
        record_service_status_change(request, user, service, prev_status, new_status, reason=reason)
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_SERVICE_STATE_CHANGED,
        record_type="service",
        record_id=service.pk,
        old_values={"status": prev_status},
        new_values={"status": new_status, "reason": reason},
    )
    return service


def record_service_status_change(
    request,
    user,
    service: InternetService,
    previous_status: str,
    new_status: str,
    *,
    reason: str = "",
) -> None:
    InternetServiceStatusHistory.objects.create(
        service=service,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        changed_by=user,
        ip_address=_ip(request),
    )


def _ip(request):
    from apps.administration.services.audit import get_client_ip

    return get_client_ip(request) if request else None


@transaction.atomic
def create_contract(request, user, data: dict) -> ServiceContract:
    service = data["service"]
    provider = data["provider"]
    if provider.pk != service.provider_id and not data.get("confirm_provider_mismatch"):
        raise ValidationError(
            "El proveedor del contrato no coincide con el del servicio. "
            "Confirme la relación para continuar."
        )
    contract = ServiceContract.objects.create(
        contract_number=data["contract_number"].strip(),
        service=service,
        provider=provider,
        start_date=data["start_date"],
        end_date=data["end_date"],
        status=data.get("status") or "active",
        observations=(data.get("observations") or "").strip(),
        created_by=user,
        updated_by=user,
    )
    contract.full_clean()
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_CONTRACT_CREATED,
        record_type="contract",
        record_id=contract.pk,
        new_values={"contract_number": contract.contract_number, "service": service.pk},
    )
    return contract


@transaction.atomic
def update_contract(request, user, contract: ServiceContract, data: dict) -> ServiceContract:
    service = data["service"]
    provider = data["provider"]
    if provider.pk != service.provider_id and not data.get("confirm_provider_mismatch"):
        raise ValidationError(
            "El proveedor del contrato no coincide con el del servicio. "
            "Confirme la relación para continuar."
        )
    contract.contract_number = data["contract_number"].strip()
    contract.service = service
    contract.provider = provider
    contract.start_date = data["start_date"]
    contract.end_date = data["end_date"]
    contract.status = data.get("status") or contract.status
    contract.observations = (data.get("observations") or "").strip()
    contract.updated_by = user
    contract.full_clean()
    contract.save()
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_CONTRACT_UPDATED,
        record_type="contract",
        record_id=contract.pk,
        new_values={"contract_number": contract.contract_number},
    )
    return contract


def _deliverable_timeliness(due_date, submitted_at: datetime | None) -> bool | None:
    if not submitted_at:
        return None
    submitted_date = timezone.localtime(submitted_at).date()
    return submitted_date <= due_date


@transaction.atomic
def create_deliverable(request, user, data: dict) -> ServiceDeliverable:
    submitted_at = data.get("submitted_at")
    on_time = _deliverable_timeliness(data["due_date"], submitted_at)
    status = data.get("status") or "pending"
    if submitted_at and on_time is False and status not in ("late",):
        status = DELIVERABLE_STATUS_LATE
    deliverable = ServiceDeliverable.objects.create(
        service=data["service"],
        contract=data.get("contract"),
        period=data["period"].strip(),
        name=data["name"].strip(),
        due_date=data["due_date"],
        submitted_at=submitted_at,
        status=status,
        observations=(data.get("observations") or "").strip(),
        submitted_on_time=on_time,
        created_by=user,
        updated_by=user,
    )
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_DELIVERABLE_CREATED,
        record_type="deliverable",
        record_id=deliverable.pk,
        new_values={"name": deliverable.name, "service": deliverable.service_id},
    )
    return deliverable


@transaction.atomic
def update_deliverable(
    request, user, deliverable: ServiceDeliverable, data: dict
) -> ServiceDeliverable:
    old_status = deliverable.status
    submitted_at = data.get("submitted_at")
    on_time = _deliverable_timeliness(data["due_date"], submitted_at)
    status = data.get("status") or deliverable.status
    if submitted_at and on_time is False:
        status = DELIVERABLE_STATUS_LATE
    deliverable.service = data["service"]
    deliverable.contract = data.get("contract")
    deliverable.period = data["period"].strip()
    deliverable.name = data["name"].strip()
    deliverable.due_date = data["due_date"]
    deliverable.submitted_at = submitted_at
    deliverable.status = status
    deliverable.observations = (data.get("observations") or "").strip()
    deliverable.submitted_on_time = on_time
    deliverable.updated_by = user
    deliverable.save()
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_DELIVERABLE_UPDATED,
        record_type="deliverable",
        record_id=deliverable.pk,
        new_values={"name": deliverable.name},
    )
    if old_status != deliverable.status:
        log_internet_event(
            request=request,
            actor=user,
            action=AUDIT_DELIVERABLE_STATE,
            record_type="deliverable",
            record_id=deliverable.pk,
            old_values={"status": old_status},
            new_values={"status": deliverable.status},
        )
    return deliverable


def _incident_duration_minutes(started_at: datetime, ended_at: datetime | None) -> int | None:
    if not ended_at:
        return None
    if ended_at < started_at:
        raise ValidationError("La fecha de término no puede ser anterior al inicio.")
    delta = ended_at - started_at
    return max(int(delta.total_seconds() // 60), 0)


@transaction.atomic
def create_incident(request, user, data: dict) -> ServiceIncident:
    ended_at = data.get("ended_at")
    started_at = data["started_at"]
    downtime = _incident_duration_minutes(started_at, ended_at)
    status = INCIDENT_STATUS_CLOSED if ended_at else INCIDENT_STATUS_OPEN
    incident = ServiceIncident.objects.create(
        ticket_code=data["ticket_code"].strip().upper(),
        service=data["service"],
        started_at=started_at,
        ended_at=ended_at,
        status=status,
        description=data["description"].strip(),
        cause=(data.get("cause") or "").strip(),
        action_taken=(data.get("action_taken") or "").strip(),
        responsible=data.get("responsible"),
        attribution=(data.get("attribution") or "").strip(),
        downtime_minutes=downtime,
        observations=(data.get("observations") or "").strip(),
        created_by=user,
        updated_by=user,
    )
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_INCIDENT_CREATED,
        record_type="incident",
        record_id=incident.pk,
        new_values={"ticket_code": incident.ticket_code},
    )
    return incident


@transaction.atomic
def update_incident(request, user, incident: ServiceIncident, data: dict) -> ServiceIncident:
    if incident.status == INCIDENT_STATUS_CLOSED and incident.ended_at:
        raise ValidationError("No se puede modificar una incidencia cerrada.")
    ended_at = data.get("ended_at")
    started_at = data["started_at"]
    downtime = _incident_duration_minutes(started_at, ended_at)
    incident.ticket_code = data["ticket_code"].strip().upper()
    incident.service = data["service"]
    incident.started_at = started_at
    incident.ended_at = ended_at
    incident.status = INCIDENT_STATUS_CLOSED if ended_at else INCIDENT_STATUS_OPEN
    incident.description = data["description"].strip()
    incident.cause = (data.get("cause") or "").strip()
    incident.action_taken = (data.get("action_taken") or "").strip()
    incident.responsible = data.get("responsible")
    incident.attribution = (data.get("attribution") or "").strip()
    incident.downtime_minutes = downtime
    incident.observations = (data.get("observations") or "").strip()
    incident.updated_by = user
    incident.save()
    action = AUDIT_INCIDENT_CLOSED if incident.status == INCIDENT_STATUS_CLOSED else AUDIT_INCIDENT_UPDATED
    log_internet_event(
        request=request,
        actor=user,
        action=action,
        record_type="incident",
        record_id=incident.pk,
        new_values={"status": incident.status, "downtime_minutes": downtime},
    )
    return incident


@transaction.atomic
def create_service_document(
    request,
    user,
    *,
    name: str,
    document_type,
    related_type: str,
    document_date,
    description: str,
    uploaded_file: UploadedFile,
    service=None,
    contract=None,
    deliverable=None,
    incident=None,
) -> ServiceDocument:
    validate_upload_extension(uploaded_file.name)
    max_mb = int(getattr(settings, "INTERNET_DOCUMENT_MAX_SIZE_MB", 10))
    if uploaded_file.size > max_mb * 1024 * 1024:
        raise ValidationError(f"El archivo supera el tamaño máximo de {max_mb} MB.")
    doc = ServiceDocument.objects.create(
        name=name.strip(),
        document_type=document_type,
        related_type=related_type,
        service=service,
        contract=contract,
        deliverable=deliverable,
        incident=incident,
        document_date=document_date,
        description=description.strip(),
        file=uploaded_file,
        original_filename=uploaded_file.name,
        uploaded_by=user,
    )
    log_internet_event(
        request=request,
        actor=user,
        action=AUDIT_DOCUMENT_UPLOADED,
        record_type="document",
        record_id=doc.pk,
        new_values={"name": doc.name, "related_type": related_type},
    )
    return doc
