ROLE_ADMINISTRADOR = "Administrador"
ROLE_USUARIO = "Usuario"

SYSTEM_ROLES = (ROLE_ADMINISTRADOR, ROLE_USUARIO)

ACTION_VIEW = "view"
ACTION_CREATE = "create"
ACTION_EDIT = "edit"
ACTION_CHANGE_STATE = "change_state"

ACTION_LABELS = {
    ACTION_VIEW: "Ver",
    ACTION_CREATE: "Crear",
    ACTION_EDIT: "Editar",
    ACTION_CHANGE_STATE: "Cambiar estado",
}

AUDIT_USER_CREATED = "user_created"
AUDIT_USER_UPDATED = "user_updated"
AUDIT_ROLE_CHANGED = "role_changed"
AUDIT_USER_ACTIVATED = "user_activated"
AUDIT_USER_DEACTIVATED = "user_deactivated"
AUDIT_PERMISSIONS_UPDATED = "permissions_updated"

AUDIT_ACTION_LABELS = {
    AUDIT_USER_CREATED: "Creación de usuario",
    AUDIT_USER_UPDATED: "Edición de usuario",
    AUDIT_ROLE_CHANGED: "Cambio de rol",
    AUDIT_USER_ACTIVATED: "Activación de cuenta",
    AUDIT_USER_DEACTIVATED: "Desactivación de cuenta",
    AUDIT_PERMISSIONS_UPDATED: "Modificación de permisos",
}

# Módulos cuyos permisos no pueden asignarse al grupo Usuario (acceso Sprint 02).
PROTECTED_MODULES_FOR_USUARIO_GROUP = frozenset(
    {"usuarios", "grupos_permisos", "auditoria", "administracion", "catalogos"}
)
