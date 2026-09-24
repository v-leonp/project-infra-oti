from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "accounts"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="accounts:login", permanent=False), name="home"),
    path("login/", views.SecureLoginView.as_view(), name="login"),
    path("logout/", views.SecureLogoutView.as_view(), name="logout"),
    path(
        "password-reset/",
        views.InstitutionalPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        views.InstitutionalPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.InstitutionalPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.InstitutionalPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("inicio/", views.WelcomeView.as_view(), name="welcome"),
]
