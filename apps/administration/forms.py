from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.administration.constants import ROLE_ADMINISTRADOR, ROLE_USUARIO, SYSTEM_ROLES

User = get_user_model()

FIELD_CLASS = "w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm focus:border-institutional-action focus:outline-none focus:ring-2 focus:ring-institutional-action/20"
SELECT_CLASS = FIELD_CLASS


class UserCreateForm(forms.Form):
    username = forms.CharField(label="Nombre de usuario", max_length=150, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    first_name = forms.CharField(label="Nombres", max_length=150, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    last_name = forms.CharField(label="Apellidos", max_length=150, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": FIELD_CLASS}))
    role = forms.ChoiceField(label="Rol", choices=[(r, r) for r in SYSTEM_ROLES], widget=forms.Select(attrs={"class": SELECT_CLASS}))
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"class": FIELD_CLASS}))
    password2 = forms.CharField(label="Confirmación de contraseña", widget=forms.PasswordInput(attrs={"class": FIELD_CLASS}))
    is_active = forms.BooleanField(label="Cuenta activa", required=False, initial=True)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if password1:
            validate_password(password1)
        return cleaned


class UserUpdateForm(forms.Form):
    first_name = forms.CharField(label="Nombres", max_length=150, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    last_name = forms.CharField(label="Apellidos", max_length=150, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": FIELD_CLASS}))
    role = forms.ChoiceField(label="Rol", choices=[(r, r) for r in SYSTEM_ROLES], widget=forms.Select(attrs={"class": SELECT_CLASS}))
    is_active = forms.BooleanField(label="Cuenta activa", required=False)

    def __init__(self, *args, user: User | None = None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if self.user and User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean(self):
        cleaned = super().clean()
        if self.user and "is_active" not in self.data:
            cleaned["is_active"] = self.user.is_active
        return cleaned


class UserPasswordChangeForm(forms.Form):
    password1 = forms.CharField(label="Nueva contraseña", widget=forms.PasswordInput(attrs={"class": FIELD_CLASS}))
    password2 = forms.CharField(label="Confirmar nueva contraseña", widget=forms.PasswordInput(attrs={"class": FIELD_CLASS}))

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if password1:
            validate_password(password1)
        return cleaned


class UserSearchForm(forms.Form):
    q = forms.CharField(label="Buscar usuarios", required=False)
    role = forms.ChoiceField(
        label="Rol",
        required=False,
        choices=[("", "Todos"), (ROLE_ADMINISTRADOR, ROLE_ADMINISTRADOR), (ROLE_USUARIO, ROLE_USUARIO)],
    )
    status = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=[("", "Todos"), ("activo", "Activo"), ("inactivo", "Inactivo")],
    )


class UserStateConfirmForm(forms.Form):
    confirm = forms.BooleanField(label="Confirmo esta acción", required=True)


class GroupPermissionsForm(forms.Form):
    group = forms.ModelChoiceField(queryset=Group.objects.filter(name__in=SYSTEM_ROLES), label="Grupo")
    description = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={"rows": 2}))
    permissions = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[],
    )
    active_tab = forms.CharField(required=False, initial="permissions")

    def __init__(self, *args, **kwargs):
        permission_choices = kwargs.pop("permission_choices", [])
        super().__init__(*args, **kwargs)
        self.fields["permissions"].choices = permission_choices


class AuditFilterForm(forms.Form):
    date_from = forms.DateField(
        label="Desde",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    date_to = forms.DateField(
        label="Hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    actor = forms.ModelChoiceField(
        label="Administrador",
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    action = forms.ChoiceField(
        label="Tipo de acción",
        required=False,
        choices=[("", "Todos")],
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )
    target_user = forms.ModelChoiceField(
        label="Usuario afectado",
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.administration.constants import AUDIT_ACTION_LABELS

        admin_users = User.objects.filter(groups__name=ROLE_ADMINISTRADOR) | User.objects.filter(is_superuser=True)
        self.fields["actor"].queryset = admin_users.distinct().order_by("username")
        self.fields["target_user"].queryset = User.objects.order_by("username")
        self.fields["action"].choices = [("", "Todos")] + [
            (key, label) for key, label in AUDIT_ACTION_LABELS.items()
        ]
