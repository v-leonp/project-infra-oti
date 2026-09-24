import re

from django import forms
from django.core.validators import URLValidator

from apps.catalogs.models import ServiceType, Site

FIELD_CLASS = "w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm focus:border-institutional-action focus:outline-none focus:ring-2 focus:ring-institutional-action/20"
SELECT_CLASS = FIELD_CLASS


class CatalogSearchForm(forms.Form):
    q = forms.CharField(label="Buscar", required=False)
    status = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=[("", "Todos"), ("activo", "Activo"), ("inactivo", "Inactivo")],
    )


class CodeNameDescriptionForm(forms.Form):
    code = forms.CharField(label="Código", max_length=50, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    name = forms.CharField(label="Nombre", max_length=255, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    description = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 3}),
    )
    is_active = forms.BooleanField(label="Activo", required=False, initial=True)


class ODSForm(CodeNameDescriptionForm):
    pass


class OESForm(CodeNameDescriptionForm):
    pass


class SiteForm(forms.Form):
    code = forms.CharField(label="Código", max_length=50, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    name = forms.CharField(label="Nombre de la sede", max_length=255, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    address = forms.CharField(label="Dirección", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    district = forms.CharField(label="Distrito", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    province = forms.CharField(label="Provincia", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    department = forms.CharField(label="Departamento", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    notes = forms.CharField(label="Observaciones", required=False, widget=forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 2}))
    is_active = forms.BooleanField(label="Activo", required=False, initial=True)


class CatalogStatusForm(forms.Form):
    code = forms.CharField(label="Código", max_length=50, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    name = forms.CharField(label="Nombre", max_length=120, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    description = forms.CharField(label="Descripción", required=False, widget=forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 2}))
    sort_order = forms.IntegerField(label="Orden de visualización", min_value=0, initial=0, widget=forms.NumberInput(attrs={"class": FIELD_CLASS}))
    is_active = forms.BooleanField(label="Registro activo", required=False, initial=True)


class ServiceTypeForm(CodeNameDescriptionForm):
    pass


class DocumentTypeForm(forms.Form):
    code = forms.CharField(label="Código", max_length=50, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    name = forms.CharField(label="Nombre", max_length=255, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    description = forms.CharField(label="Descripción", required=False, widget=forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 2}))
    allowed_extensions = forms.CharField(label="Extensiones permitidas", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    is_active = forms.BooleanField(label="Activo", required=False, initial=True)


class ProviderSearchForm(CatalogSearchForm):
    service_type = forms.ModelChoiceField(
        label="Tipo de servicio",
        queryset=ServiceType.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": SELECT_CLASS}),
    )


class ProviderForm(forms.Form):
    code = forms.CharField(label="Código", max_length=50, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    is_active = forms.BooleanField(label="Activo", required=False, initial=True)
    legal_name = forms.CharField(label="Razón social", max_length=255, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    ruc = forms.CharField(label="RUC", max_length=11, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    service_types = forms.ModelMultipleChoiceField(
        label="Tipo de servicio",
        queryset=ServiceType.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={"class": SELECT_CLASS, "size": 4}),
    )
    phone = forms.CharField(label="Teléfono", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    main_contact = forms.CharField(label="Contacto principal", max_length=255, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    address = forms.CharField(label="Dirección", required=False, widget=forms.Textarea(attrs={"class": FIELD_CLASS, "rows": 2}))
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": FIELD_CLASS}))
    website = forms.CharField(label="Sitio web", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))

    def clean_ruc(self):
        ruc = re.sub(r"\D", "", self.cleaned_data.get("ruc", ""))
        if len(ruc) != 11:
            raise forms.ValidationError("El RUC debe tener 11 dígitos numéricos.")
        return ruc

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and not re.match(r"^[\d\s+\-()]{7,30}$", phone):
            raise forms.ValidationError("Ingrese un teléfono válido.")
        return phone

    def clean_website(self):
        website = self.cleaned_data.get("website", "").strip()
        if not website:
            return ""
        validator = URLValidator()
        if not website.startswith(("http://", "https://")):
            website = f"https://{website}"
        validator(website)
        return website

    def clean_service_types(self):
        types = self.cleaned_data.get("service_types")
        if not types:
            raise forms.ValidationError("Seleccione al menos un tipo de servicio.")
        return types


class ResponsibleForm(forms.Form):
    code = forms.CharField(label="Código", max_length=50, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    first_name = forms.CharField(label="Nombres", max_length=120, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    last_name = forms.CharField(label="Apellidos", max_length=120, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    job_title = forms.CharField(label="Cargo o función", max_length=120, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"class": FIELD_CLASS}))
    phone = forms.CharField(label="Teléfono", required=False, widget=forms.TextInput(attrs={"class": FIELD_CLASS}))
    site = forms.ModelChoiceField(label="Sede", queryset=Site.objects.filter(is_active=True), widget=forms.Select(attrs={"class": SELECT_CLASS}))
    is_active = forms.BooleanField(label="Activo", required=False, initial=True)


class StateConfirmForm(forms.Form):
    confirm = forms.BooleanField(label="Confirmo esta acción", required=True)
