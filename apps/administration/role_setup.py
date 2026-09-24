from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.administration.constants import ROLE_ADMINISTRADOR, ROLE_USUARIO, SYSTEM_ROLES
from apps.administration.models import AccessControlMeta


def ensure_system_groups() -> dict[str, Group]:
    groups: dict[str, Group] = {}
    for role_name in SYSTEM_ROLES:
        group, _ = Group.objects.get_or_create(name=role_name)
        groups[role_name] = group
    return groups


def _all_module_permissions() -> list[Permission]:
    content_type = ContentType.objects.get_for_model(AccessControlMeta)
    return list(Permission.objects.filter(content_type=content_type))


def ensure_group_profiles(groups: dict[str, Group]) -> None:
    from apps.administration.models import GroupProfile

    defaults = {
        "Administrador": "Acceso completo a la administración del sistema.",
        "Usuario": "Acceso operativo sin funciones de administración.",
    }
    for name, group in groups.items():
        GroupProfile.objects.get_or_create(
            group=group,
            defaults={"description": defaults.get(name, "")},
        )


def assign_default_group_permissions(groups: dict[str, Group]) -> None:
    permissions = _all_module_permissions()
    admin_group = groups[ROLE_ADMINISTRADOR]
    admin_group.permissions.set(permissions)

    usuario_group = groups[ROLE_USUARIO]
    protected_prefixes = ("usuarios_", "grupos_permisos_", "auditoria_", "catalogos_")
    usuario_group.permissions.set(
        [p for p in permissions if not p.codename.startswith(protected_prefixes)]
    )


def setup_roles_and_permissions() -> None:
    groups = ensure_system_groups()
    ensure_group_profiles(groups)
    assign_default_group_permissions(groups)


def permission_for_codename(codename: str) -> Permission | None:
    content_type = ContentType.objects.get_for_model(AccessControlMeta)
    return Permission.objects.filter(content_type=content_type, codename=codename).first()


def codenames_for_group(group: Group) -> set[str]:
    return set(group.permissions.values_list("codename", flat=True))
