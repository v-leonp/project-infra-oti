from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from apps.internet.access import is_internet_module_user


class InternetModuleUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Solo usuarios del grupo Usuario (operativos)."""

    def test_func(self):
        return is_internet_module_user(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied
