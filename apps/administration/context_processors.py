from apps.administration.access import is_system_administrator
from apps.administration.services.users import get_user_role_name


def administration(request):
    user = request.user
    if not user.is_authenticated:
        return {
            "is_system_administrator": False,
            "current_user_role_label": "",
            "current_user_initials": "",
        }
    first = (user.first_name or user.username)[:1].upper()
    last = (user.last_name or "")[:1].upper()
    initials = (first + last) or user.username[:2].upper()
    return {
        "is_system_administrator": is_system_administrator(user),
        "current_user_role_label": get_user_role_name(user)
        or ("Superusuario" if user.is_superuser else "Usuario"),
        "current_user_initials": initials,
    }
