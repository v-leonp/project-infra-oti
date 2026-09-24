from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm

GENERIC_AUTH_ERROR = "Usuario o contraseña incorrectos."


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión con mensajes genéricos y etiquetas en español."""

    error_messages = {
        "invalid_login": GENERIC_AUTH_ERROR,
        "inactive": "Esta cuenta está inactiva.",
    }

    username = forms.CharField(
        label="Usuario",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "class": "login-input",
                "placeholder": "",
            }
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "login-input",
            }
        ),
    )


class InstitutionalPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "class": "login-input",
            }
        ),
    )
