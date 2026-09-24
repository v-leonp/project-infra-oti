from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError

from apps.catalogs.models import ODS, OES, DocumentType, Provider, Responsible, Site
from apps.internet.constants import (
    CONTRACT_STATUS_CHOICES,
    DELIVERABLE_STATUS_CHOICES,
    DOCUMENT_RELATED_CHOICES,
    LINK_TYPE_CHOICES,
    SERVICE_STATUS_FILTER_CHOICES,
)
from apps.internet.models import (
    InternetService,
    ServiceContract,
    ServiceDeliverable,
    ServiceDocument,
    ServiceIncident,
)
from apps.internet.validators import validate_public_ip


class ServiceSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Buscar")
    site = forms.ModelChoiceField(queryset=Site.objects.filter(is_active=True), required=False, label="Sede")
    provider = forms.ModelChoiceField(
        queryset=Provider.objects.filter(is_active=True), required=False, label="Proveedor"
    )
    status = forms.ChoiceField(choices=SERVICE_STATUS_FILTER_CHOICES, required=False, label="Estado")
    ods = forms.ModelChoiceField(queryset=ODS.objects.filter(is_active=True), required=False, label="ODS")
    oes = forms.ModelChoiceField(queryset=OES.objects.filter(is_active=True), required=False, label="OES")
    validity = forms.ChoiceField(
        required=False,
        label="Vigencia",
        choices=[
            ("", "Todas"),
            ("active", "Vigentes"),
            ("expiring", "Próximas a vencer"),
            ("expired", "Vencidas"),
        ],
    )
    order = forms.ChoiceField(
        required=False,
        choices=[
            ("code", "Código (A-Z)"),
            ("-code", "Código (Z-A)"),
            ("end_date", "Vigencia (asc)"),
            ("-end_date", "Vigencia (desc)"),
        ],
        initial="code",
    )


class InternetServiceForm(forms.ModelForm):
    ods_oes_type = forms.ChoiceField(
        choices=[("ods", "ODS"), ("oes", "OES")],
        label="Tipo ODS/OES",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = InternetService
        fields = [
            "code",
            "ods",
            "oes",
            "site",
            "provider",
            "responsible",
            "link_type",
            "contracted_speed",
            "speed_unit",
            "public_ip",
            "circuit_id",
            "connection_medium",
            "technical_observations",
            "start_date",
            "end_date",
            "observations",
            "marked_with_observations",
            "is_active",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "observations": forms.Textarea(attrs={"rows": 4, "maxlength": 500}),
            "technical_observations": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget_class = "w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
        for name, field in self.fields.items():
            if name == "ods_oes_type":
                continue
            w = field.widget
            w.attrs.setdefault("class", widget_class)
        self.fields["ods"].queryset = ODS.objects.filter(is_active=True)
        self.fields["oes"].queryset = OES.objects.filter(is_active=True)
        self.fields["site"].queryset = Site.objects.filter(is_active=True)
        self.fields["provider"].queryset = Provider.objects.filter(is_active=True)
        self.fields["responsible"].queryset = Responsible.objects.filter(is_active=True)
        self.fields["link_type"].choices = LINK_TYPE_CHOICES
        if self.instance and self.instance.pk:
            self.fields["ods_oes_type"].initial = "ods" if self.instance.ods_id else "oes"

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().upper()
        qs = InternetService.objects.filter(code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe un servicio con este código.")
        return code

    def clean_public_ip(self):
        value = self.cleaned_data.get("public_ip")
        validate_public_ip(value)
        return value

    def clean(self):
        cleaned = super().clean()
        ods = cleaned.get("ods")
        oes = cleaned.get("oes")
        tipo = cleaned.get("ods_oes_type")
        if tipo == "ods":
            cleaned["oes"] = None
            if not ods:
                self.add_error("ods", "Seleccione un ODS.")
        else:
            cleaned["ods"] = None
            if not oes:
                self.add_error("oes", "Seleccione un OES.")
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "La fecha de término no puede ser anterior a la de inicio.")
        speed = cleaned.get("contracted_speed")
        if speed is not None and speed <= 0:
            self.add_error("contracted_speed", "La velocidad debe ser mayor que cero.")
        return cleaned


class ServiceStateForm(forms.Form):
    is_active = forms.BooleanField(required=False, label="Servicio activo")
    marked_with_observations = forms.BooleanField(required=False, label="Marcar con observaciones")
    reason = forms.CharField(required=False, max_length=255, label="Motivo")


class ServiceContractForm(forms.ModelForm):
    confirm_provider_mismatch = forms.BooleanField(
        required=False,
        label="Confirmo que el proveedor del contrato difiere del servicio",
    )

    class Meta:
        model = ServiceContract
        fields = [
            "contract_number",
            "service",
            "provider",
            "start_date",
            "end_date",
            "status",
            "observations",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "observations": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = InternetService.objects.filter(is_active=True)
        self.fields["provider"].queryset = Provider.objects.filter(is_active=True)
        self.fields["status"].choices = CONTRACT_STATUS_CHOICES

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "La fecha de término no puede ser anterior a la de inicio.")
        service = cleaned.get("service")
        provider = cleaned.get("provider")
        if service and provider and service.provider_id != provider.pk:
            if not cleaned.get("confirm_provider_mismatch"):
                raise ValidationError(
                    "El proveedor no coincide con el del servicio. Marque la confirmación."
                )
        return cleaned


class ServiceDeliverableForm(forms.ModelForm):
    class Meta:
        model = ServiceDeliverable
        fields = [
            "service",
            "contract",
            "period",
            "name",
            "due_date",
            "submitted_at",
            "status",
            "observations",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "submitted_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "observations": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = InternetService.objects.filter(is_active=True)
        self.fields["contract"].queryset = ServiceContract.objects.filter(is_active=True)
        self.fields["status"].choices = DELIVERABLE_STATUS_CHOICES


class ServiceIncidentForm(forms.ModelForm):
    class Meta:
        model = ServiceIncident
        fields = [
            "ticket_code",
            "service",
            "started_at",
            "ended_at",
            "description",
            "cause",
            "action_taken",
            "responsible",
            "attribution",
            "observations",
        ]
        widgets = {
            "started_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ended_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "cause": forms.Textarea(attrs={"rows": 2}),
            "action_taken": forms.Textarea(attrs={"rows": 2}),
            "observations": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["service"].queryset = InternetService.objects.filter(is_active=True)
        self.fields["responsible"].queryset = Responsible.objects.filter(is_active=True)
        self.fields["ended_at"].required = False

    def clean(self):
        cleaned = super().clean()
        started = cleaned.get("started_at")
        ended = cleaned.get("ended_at")
        if started and ended and ended < started:
            self.add_error("ended_at", "La fecha de término no puede ser anterior al inicio.")
        return cleaned


class ServiceDocumentForm(forms.ModelForm):
    class Meta:
        model = ServiceDocument
        fields = [
            "name",
            "document_type",
            "related_type",
            "service",
            "contract",
            "deliverable",
            "incident",
            "document_date",
            "description",
            "file",
        ]
        widgets = {
            "document_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document_type"].queryset = DocumentType.objects.filter(is_active=True)
        self.fields["related_type"].choices = DOCUMENT_RELATED_CHOICES
        self.fields["service"].queryset = InternetService.objects.all()
        self.fields["contract"].queryset = ServiceContract.objects.filter(is_active=True)
        self.fields["deliverable"].queryset = ServiceDeliverable.objects.filter(is_active=True)
        self.fields["incident"].queryset = ServiceIncident.objects.filter(is_active=True)
        self.fields["service"].required = False
        self.fields["contract"].required = False
        self.fields["deliverable"].required = False
        self.fields["incident"].required = False

    def clean(self):
        cleaned = super().clean()
        related = cleaned.get("related_type")
        mapping = {
            "service": cleaned.get("service"),
            "contract": cleaned.get("contract"),
            "deliverable": cleaned.get("deliverable"),
            "incident": cleaned.get("incident"),
        }
        if not mapping.get(related):
            self.add_error(related, "Seleccione el registro relacionado.")
        file = cleaned.get("file")
        if file:
            from apps.internet.validators import validate_upload_extension

            validate_upload_extension(file.name)
        return cleaned


class ReportFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Búsqueda")
    ods = forms.ModelChoiceField(queryset=ODS.objects.filter(is_active=True), required=False)
    oes = forms.ModelChoiceField(queryset=OES.objects.filter(is_active=True), required=False)
    site = forms.ModelChoiceField(queryset=Site.objects.filter(is_active=True), required=False)
    provider = forms.ModelChoiceField(queryset=Provider.objects.filter(is_active=True), required=False)
    status = forms.ChoiceField(choices=SERVICE_STATUS_FILTER_CHOICES, required=False)
    link_type = forms.ChoiceField(choices=[("", "Todos")] + list(LINK_TYPE_CHOICES), required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    validity = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Todas"),
            ("active", "Vigentes"),
            ("expiring", "Próximas a vencer"),
            ("expired", "Vencidas"),
        ],
    )
    responsible = forms.ModelChoiceField(
        queryset=Responsible.objects.filter(is_active=True), required=False
    )
    report_type = forms.ChoiceField(
        choices=[
            ("active", "Servicios activos"),
            ("expiring", "Próximos a vencer"),
            ("expired", "Vencidos"),
            ("observations", "Con observaciones"),
            ("incidents", "Incidencias"),
            ("deliverables", "Entregables"),
        ],
        initial="active",
    )
