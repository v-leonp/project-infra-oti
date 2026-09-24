from __future__ import annotations

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.administration.constants import (
    AUDIT_PERMISSIONS_UPDATED,
    PROTECTED_MODULES_FOR_USUARIO_GROUP,
    ROLE_USUARIO,
)
from apps.administration.role_setup import codenames_for_group, permission_for_codename
from apps.administration.services.audit import log_audit_event


class GroupPermissionError(ValidationError):
    pass


def _codename_is_protected_for_usuario(codename: str) -> bool:
    for module_code in PROTECTED_MODULES_FOR_USUARIO_GROUP:
        if codename.startswith(f"{module_code}_"):
            return True
    return False


def filter_allowed_codenames_for_group(group: Group, codenames: set[str]) -> set[str]:
    if group.name != ROLE_USUARIO:
        return codenames
    return {code for code in codenames if not _codename_is_protected_for_usuario(code)}


@transaction.atomic
def update_group_permissions(
    *,
    actor,
    group: Group,
    description: str,
    selected_codenames: set[str],
    ip_address: str | None = None,
) -> Group:
    allowed = filter_allowed_codenames_for_group(group, selected_codenames)
    if group.name == ROLE_USUARIO and allowed != selected_codenames:
        raise GroupPermissionError(
            "El grupo Usuario no puede recibir permisos de administración del sistema."
        )

    old_codenames = sorted(codenames_for_group(group))
    permissions = []
    for codename in allowed:
        permission = permission_for_codename(codename)
        if permission:
            permissions.append(permission)

    group.permissions.set(permissions)
    from apps.administration.models import GroupProfile

    profile, _ = GroupProfile.objects.get_or_create(group=group)
    old_description = profile.description
    profile.description = description
    profile.save(update_fields=["description"])

    new_codenames = sorted(codenames_for_group(group))
    log_audit_event(
        actor=actor,
        action=AUDIT_PERMISSIONS_UPDATED,
        target_group=group,
        old_values={"permissions": old_codenames, "description": old_description},
        new_values={"permissions": new_codenames, "description": description},
        ip_address=ip_address,
    )
    return group


def build_matrix_state(group: Group) -> dict:
    from apps.administration.permissions_registry import iter_matrix_cells

    assigned = codenames_for_group(group)
    rows = []
    for module, action, codename in iter_matrix_cells():
        rows.append(
            {
                "module_code": module["code"],
                "module_label": module["label"],
                "action": action,
                "codename": codename,
                "checked": codename in assigned,
            }
        )
    return {"rows": rows, "assigned": assigned}
