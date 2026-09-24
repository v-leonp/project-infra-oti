from django import template

from apps.internet.constants import SERVICE_STATUS_LABELS

register = template.Library()


@register.filter
def service_status_label(code: str) -> str:
    return SERVICE_STATUS_LABELS.get(code, code)


@register.filter
def service_status_badge(code: str) -> str:
    mapping = {
        "active": "bg-emerald-100 text-emerald-800 ring-emerald-200",
        "expiring": "bg-amber-100 text-amber-900 ring-amber-200",
        "observations": "bg-red-100 text-red-800 ring-red-200",
        "expired": "bg-slate-200 text-slate-800 ring-slate-300",
        "inactive": "bg-slate-100 text-slate-600 ring-slate-200",
    }
    return mapping.get(code, "bg-slate-100 text-slate-700 ring-slate-200")
