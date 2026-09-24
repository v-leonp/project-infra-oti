from django.contrib.auth.models import AnonymousUser

from apps.administration.access import is_system_administrator
from apps.administration.constants import ROLE_USUARIO


def is_internet_module_user(user) -> bool:
    """
    Acceso exclusivo del grupo Usuario (sin superusuario ni Administrador).
    """
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    if user.is_superuser or is_system_administrator(user):
        return False
    return user.groups.filter(name=ROLE_USUARIO).exists()
