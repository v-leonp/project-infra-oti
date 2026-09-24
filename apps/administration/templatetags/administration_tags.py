from django import template

from apps.administration.constants import AUDIT_ACTION_LABELS
from apps.administration.services.users import get_user_role_name
from apps.catalogs.constants import AUDIT_CATALOG_ACTION_LABELS
from apps.internet.constants import AUDIT_INTERNET_ACTION_LABELS

register = template.Library()


@register.filter
def user_role(user):
    return get_user_role_name(user) or "—"


@register.filter
def audit_action_label(action_code):
    return AUDIT_CATALOG_ACTION_LABELS.get(
        action_code,
        AUDIT_INTERNET_ACTION_LABELS.get(
            action_code, AUDIT_ACTION_LABELS.get(action_code, action_code)
        ),
    )


@register.filter
def role_badge_classes(role_name):
    if role_name == "Administrador":
        return "bg-violet-100 text-violet-800 ring-violet-200"
    if role_name == "Usuario":
        return "bg-sky-100 text-sky-800 ring-sky-200"
    return "bg-slate-100 text-slate-700 ring-slate-200"
