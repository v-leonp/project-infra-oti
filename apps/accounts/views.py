from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import InstitutionalPasswordResetForm, LoginForm


class SecureLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session.cycle_key()
        return response


class SecureLogoutView(LogoutView):
    http_method_names = ["post", "options", "head"]


class WelcomeView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/welcome.html"


class InstitutionalPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    form_class = InstitutionalPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class InstitutionalPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class InstitutionalPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class InstitutionalPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
