"""Fuente centralizada de módulos y permisos del sistema."""

from apps.administration.constants import (
    ACTION_CHANGE_STATE,
    ACTION_CREATE,
    ACTION_EDIT,
    ACTION_LABELS,
    ACTION_VIEW,
)

MODULES = (
    {"code": "usuarios", "label": "Usuarios"},
    {"code": "grupos_permisos", "label": "Grupos y permisos"},
    {"code": "auditoria", "label": "Auditoría"},
    {"code": "internet", "label": "Internet"},
    {"code": "documentos", "label": "Documentos"},
    {"code": "reportes", "label": "Reportes"},
    {"code": "catalogos", "label": "Catálogos"},
)

ACTIONS = (ACTION_VIEW, ACTION_CREATE, ACTION_EDIT, ACTION_CHANGE_STATE)


def permission_codename(module_code: str, action: str) -> str:
    return f"{module_code}_{action}"


def permission_label(module_label: str, action: str) -> str:
    return f"{ACTION_LABELS[action]} — {module_label}"


def build_custom_permissions() -> list[tuple[str, str]]:
    permissions: list[tuple[str, str]] = []
    for module in MODULES:
        for action in ACTIONS:
            permissions.append(
                (
                    permission_codename(module["code"], action),
                    permission_label(module["label"], action),
                )
            )
    return permissions


def iter_matrix_cells():
    """Itera (módulo, acción, codename) para la matriz de permisos."""
    for module in MODULES:
        for action in ACTIONS:
            yield module, action, permission_codename(module["code"], action)
