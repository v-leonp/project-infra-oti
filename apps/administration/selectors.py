from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import Prefetch, Q, QuerySet

from apps.administration.constants import ROLE_ADMINISTRADOR, ROLE_USUARIO, SYSTEM_ROLES
from apps.administration.models import AuditLog

User = get_user_model()


def user_list_queryset(
    *,
    search: str = "",
    role: str = "",
    status: str = "",
) -> QuerySet:
    qs = (
        User.objects.all()
        .prefetch_related(Prefetch("groups", queryset=Group.objects.filter(name__in=SYSTEM_ROLES)))
        .order_by("username")
    )

    if search:
        term = search.strip()
        qs = qs.filter(
            Q(username__icontains=term)
            | Q(first_name__icontains=term)
            | Q(last_name__icontains=term)
            | Q(email__icontains=term)
        )

    if role == ROLE_ADMINISTRADOR:
        qs = qs.filter(groups__name=ROLE_ADMINISTRADOR)
    elif role == ROLE_USUARIO:
        qs = qs.filter(groups__name=ROLE_USUARIO)

    if status == "activo":
        qs = qs.filter(is_active=True)
    elif status == "inactivo":
        qs = qs.filter(is_active=False)

    return qs.distinct()


def audit_log_queryset(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    actor_id: int | None = None,
    action: str = "",
    target_user_id: int | None = None,
) -> QuerySet:
    qs = AuditLog.objects.select_related("actor", "target_user", "target_group")
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)
    if actor_id:
        qs = qs.filter(actor_id=actor_id)
    if action:
        qs = qs.filter(action=action)
    if target_user_id:
        qs = qs.filter(target_user_id=target_user_id)
    return qs
