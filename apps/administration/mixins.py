from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class SystemAdministratorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Solo Administradores (grupo) o superusuarios."""

    def test_func(self):
        from apps.administration.access import is_system_administrator

        return is_system_administrator(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied
