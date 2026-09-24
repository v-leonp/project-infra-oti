from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.internet.constants import (
    CONTRACT_STATUS_CHOICES,
    DELIVERABLE_STATUS_CHOICES,
    DOCUMENT_RELATED_CHOICES,
    INCIDENT_STATUS_CHOICES,
    LINK_TYPE_CHOICES,
)
from apps.internet.state import compute_service_status


def private_document_upload_to(instance: ServiceDocument, filename: str) -> str:
    ext = Path(filename).suffix.lower().lstrip(".")
    safe = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return f"internet/documents/{safe}"


class InternetService(models.Model):
    code = models.CharField(max_length=50, unique=True)
    ods = models.ForeignKey(
        "catalogs.ODS",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="internet_services",
    )
    oes = models.ForeignKey(
        "catalogs.OES",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="internet_services",
    )
    site = models.ForeignKey("catalogs.Site", on_delete=models.PROTECT, related_name="internet_services")
    provider = models.ForeignKey(
        "catalogs.Provider", on_delete=models.PROTECT, related_name="internet_services"
    )
    responsible = models.ForeignKey(
        "catalogs.Responsible",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="internet_services",
    )
    link_type = models.CharField(max_length=40, choices=LINK_TYPE_CHOICES)
    contracted_speed = models.DecimalField(max_digits=12, decimal_places=2)
    speed_unit = models.CharField(max_length=20, default="Mbps")
    public_ip = models.GenericIPAddressField(null=True, blank=True)
    circuit_id = models.CharField(max_length=120, blank=True, default="")
    connection_medium = models.CharField(max_length=120, blank=True, default="")
    technical_observations = models.TextField(blank=True, default="")
    start_date = models.DateField()
    end_date = models.DateField()
    observations = models.TextField(max_length=500, blank=True, default="")
    marked_with_observations = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_services_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_services_updated",
    )

    class Meta:
        ordering = ("code",)
        verbose_name = "Servicio de Internet"
        verbose_name_plural = "Servicios de Internet"
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["end_date"]),
            models.Index(fields=["is_active", "end_date"]),
            models.Index(fields=["site"]),
            models.Index(fields=["provider"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=models.F("start_date")),
                name="internet_service_end_after_start",
            ),
            models.CheckConstraint(
                condition=Q(contracted_speed__gt=0),
                name="internet_service_speed_positive",
            ),
            models.CheckConstraint(
                condition=Q(ods__isnull=False) | Q(oes__isnull=False),
                name="internet_service_ods_or_oes_required",
            ),
        ]

    def __str__(self) -> str:
        return self.code

    @property
    def ods_oes_label(self) -> str:
        if self.ods_id:
            return f"{self.ods.code} — {self.ods.name}"
        if self.oes_id:
            return f"{self.oes.code} — {self.oes.name}"
        return "—"

    @property
    def display_status(self) -> str:
        return compute_service_status(
            is_active=self.is_active,
            end_date=self.end_date,
            marked_with_observations=self.marked_with_observations,
        )

    def clean(self):
        super().clean()
        if not self.ods_id and not self.oes_id:
            raise ValidationError("Debe seleccionar ODS u OES.")
        if self.ods_id and self.oes_id:
            raise ValidationError("Seleccione solo ODS u OES, no ambos.")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("La fecha de término no puede ser anterior a la de inicio.")


class InternetServiceStatusHistory(models.Model):
    service = models.ForeignKey(
        InternetService, on_delete=models.CASCADE, related_name="status_history"
    )
    previous_status = models.CharField(max_length=32)
    new_status = models.CharField(max_length=32)
    reason = models.CharField(max_length=255, blank=True, default="")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-changed_at",)


class ServiceContract(models.Model):
    contract_number = models.CharField(max_length=120)
    service = models.ForeignKey(
        InternetService, on_delete=models.PROTECT, related_name="contracts"
    )
    provider = models.ForeignKey("catalogs.Provider", on_delete=models.PROTECT, related_name="+")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS_CHOICES, default="active")
    observations = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_contracts_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_contracts_updated",
    )

    class Meta:
        ordering = ("-start_date",)
        constraints = [
            models.CheckConstraint(
                condition=Q(end_date__gte=models.F("start_date")),
                name="internet_contract_end_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["contract_number"]),
            models.Index(fields=["service", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.contract_number


class ServiceDeliverable(models.Model):
    service = models.ForeignKey(
        InternetService, on_delete=models.PROTECT, related_name="deliverables"
    )
    contract = models.ForeignKey(
        ServiceContract,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="deliverables",
    )
    period = models.CharField(max_length=120)
    name = models.CharField(max_length=255)
    due_date = models.DateField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=DELIVERABLE_STATUS_CHOICES, default="pending")
    observations = models.TextField(blank=True, default="")
    submitted_on_time = models.BooleanField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_deliverables_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_deliverables_updated",
    )

    class Meta:
        ordering = ("-due_date",)
        indexes = [models.Index(fields=["service", "status"])]


class ServiceIncident(models.Model):
    ticket_code = models.CharField(max_length=50, unique=True)
    service = models.ForeignKey(
        InternetService, on_delete=models.PROTECT, related_name="incidents"
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=INCIDENT_STATUS_CHOICES, default="open")
    description = models.TextField()
    cause = models.TextField(blank=True, default="")
    action_taken = models.TextField(blank=True, default="")
    responsible = models.ForeignKey(
        "catalogs.Responsible",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="internet_incidents",
    )
    attribution = models.CharField(max_length=255, blank=True, default="")
    downtime_minutes = models.PositiveIntegerField(null=True, blank=True)
    observations = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_incidents_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_incidents_updated",
    )

    class Meta:
        ordering = ("-started_at",)
        indexes = [models.Index(fields=["ticket_code"]), models.Index(fields=["service", "status"])]


class ServiceDocument(models.Model):
    name = models.CharField(max_length=255)
    document_type = models.ForeignKey(
        "catalogs.DocumentType", on_delete=models.PROTECT, related_name="internet_documents"
    )
    related_type = models.CharField(max_length=20, choices=DOCUMENT_RELATED_CHOICES)
    service = models.ForeignKey(
        InternetService,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    contract = models.ForeignKey(
        ServiceContract,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    deliverable = models.ForeignKey(
        ServiceDeliverable,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    incident = models.ForeignKey(
        ServiceIncident,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documents",
    )
    document_date = models.DateField()
    description = models.TextField(blank=True, default="")
    file = models.FileField(upload_to=private_document_upload_to)
    original_filename = models.CharField(max_length=255, blank=True, default="")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="internet_documents_uploaded",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at",)
        indexes = [models.Index(fields=["related_type", "uploaded_at"])]
