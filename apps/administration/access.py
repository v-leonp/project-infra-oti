from django.contrib.auth.models import AnonymousUser

from apps.administration.constants import ROLE_ADMINISTRADOR


def is_system_administrator(user) -> bool:
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=ROLE_ADMINISTRADOR).exists()
