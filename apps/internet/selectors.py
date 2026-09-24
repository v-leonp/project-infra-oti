from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.internet.constants import (
    SERVICE_STATUS_ACTIVE,
    SERVICE_STATUS_EXPIRED,
    SERVICE_STATUS_EXPIRING,
    SERVICE_STATUS_INACTIVE,
    SERVICE_STATUS_OBSERVATIONS,
)
from apps.internet.models import (
    InternetService,
    ServiceContract,
    ServiceDeliverable,
    ServiceDocument,
    ServiceIncident,
)
from apps.internet.state import expiry_warning_days


def service_base_qs() -> QuerySet[InternetService]:
    return InternetService.objects.select_related(
        "ods",
        "oes",
        "site",
        "provider",
        "responsible",
    )


def _status_q(status_code: str, today: date) -> Q:
    warning = expiry_warning_days()
    expiring_end = today + timedelta(days=warning)
    if status_code == SERVICE_STATUS_INACTIVE:
        return Q(is_active=False)
    if status_code == SERVICE_STATUS_OBSERVATIONS:
        return Q(is_active=True, marked_with_observations=True)
    if status_code == SERVICE_STATUS_EXPIRED:
        return Q(is_active=True, marked_with_observations=False, end_date__lt=today)
    if status_code == SERVICE_STATUS_EXPIRING:
        return Q(
            is_active=True,
            marked_with_observations=False,
            end_date__gte=today,
            end_date__lte=expiring_end,
        )
    if status_code == SERVICE_STATUS_ACTIVE:
        return Q(
            is_active=True,
            marked_with_observations=False,
            end_date__gt=expiring_end,
        )
    return Q()


def filter_services(
    *,
    search: str = "",
    site_id: str | None = None,
    provider_id: str | None = None,
    status: str = "",
    ods_id: str | None = None,
    oes_id: str | None = None,
    validity: str = "",
    order: str = "code",
) -> QuerySet[InternetService]:
    qs = service_base_qs()
    today = timezone.localdate()
    if search:
        term = search.strip()
        qs = qs.filter(
            Q(code__icontains=term)
            | Q(site__name__icontains=term)
            | Q(site__code__icontains=term)
            | Q(provider__legal_name__icontains=term)
            | Q(provider__code__icontains=term)
            | Q(responsible__first_name__icontains=term)
            | Q(responsible__last_name__icontains=term)
            | Q(public_ip__icontains=term)
            | Q(contracts__contract_number__icontains=term)
        ).distinct()
    if site_id:
        qs = qs.filter(site_id=site_id)
    if provider_id:
        qs = qs.filter(provider_id=provider_id)
    if ods_id:
        qs = qs.filter(ods_id=ods_id)
    if oes_id:
        qs = qs.filter(oes_id=oes_id)
    if status:
        qs = qs.filter(_status_q(status, today))
    if validity == "active":
        qs = qs.filter(is_active=True, end_date__gte=today)
    elif validity == "expired":
        qs = qs.filter(end_date__lt=today)
    elif validity == "expiring":
        qs = qs.filter(
            is_active=True,
            end_date__gte=today,
            end_date__lte=today + timedelta(days=expiry_warning_days()),
        )
    order_map = {
        "code": "code",
        "-code": "-code",
        "end_date": "end_date",
        "-end_date": "-end_date",
        "site": "site__name",
        "provider": "provider__legal_name",
    }
    qs = qs.order_by(order_map.get(order, "code"))
    return qs


def service_kpis() -> dict[str, int]:
    today = timezone.localdate()
    warning = expiry_warning_days()
    expiring_end = today + timedelta(days=warning)
    base = InternetService.objects.all()
    return {
        "active": base.filter(
            is_active=True,
            marked_with_observations=False,
            end_date__gt=expiring_end,
        ).count(),
        "expiring": base.filter(
            is_active=True,
            marked_with_observations=False,
            end_date__gte=today,
            end_date__lte=expiring_end,
        ).count(),
        "observations": base.filter(is_active=True, marked_with_observations=True).count(),
    }


def contracts_qs() -> QuerySet[ServiceContract]:
    return ServiceContract.objects.select_related("service", "provider").filter(is_active=True)


def deliverables_qs() -> QuerySet[ServiceDeliverable]:
    return ServiceDeliverable.objects.select_related("service", "contract").filter(is_active=True)


def incidents_qs() -> QuerySet[ServiceIncident]:
    return ServiceIncident.objects.select_related("service", "responsible").filter(is_active=True)


def documents_qs() -> QuerySet[ServiceDocument]:
    return ServiceDocument.objects.select_related(
        "document_type", "service", "contract", "deliverable", "incident", "uploaded_by"
    )


def report_services_qs(filters: dict) -> QuerySet[InternetService]:
    return filter_services(
        search=filters.get("q", ""),
        site_id=filters.get("site") or None,
        provider_id=filters.get("provider") or None,
        status=filters.get("status", ""),
        ods_id=filters.get("ods") or None,
        oes_id=filters.get("oes") or None,
        validity=filters.get("validity", ""),
        order=filters.get("order", "code"),
    )


def annotate_status_counts(qs: QuerySet[InternetService]) -> dict[str, int]:
    today = timezone.localdate()
    counts = {"total": qs.count()}
    for key in (
        SERVICE_STATUS_ACTIVE,
        SERVICE_STATUS_EXPIRING,
        SERVICE_STATUS_OBSERVATIONS,
        SERVICE_STATUS_EXPIRED,
        SERVICE_STATUS_INACTIVE,
    ):
        counts[key] = qs.filter(_status_q(key, today)).count()
    return counts


def service_snapshot(service: InternetService) -> dict:
    return {
        "code": service.code,
        "ods_oes": service.ods_oes_label,
        "site": service.site_id,
        "provider": service.provider_id,
        "display_status": service.display_status,
        "start_date": str(service.start_date),
        "end_date": str(service.end_date),
    }
