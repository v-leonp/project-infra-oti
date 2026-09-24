from django.conf import settings
from django.db import models


class CatalogTimestampedModel(models.Model):
    code = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.code}"


class ODS(CatalogTimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "ODS"
        verbose_name_plural = "ODS"
        ordering = ("code",)


class OES(CatalogTimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "OES"
        verbose_name_plural = "OES"
        ordering = ("code",)


class Site(CatalogTimestampedModel):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True, default="")
    district = models.CharField(max_length=120, blank=True, default="")
    province = models.CharField(max_length=120, blank=True, default="")
    department = models.CharField(max_length=120, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        ordering = ("code",)


class ServiceType(CatalogTimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Tipo de servicio"
        verbose_name_plural = "Tipos de servicio"
        ordering = ("code",)


class CatalogStatus(CatalogTimestampedModel):
    """Estados de negocio reutilizables (distinto de is_active de vigencia)."""

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Estado (catálogo)"
        verbose_name_plural = "Estados (catálogo)"
        ordering = ("sort_order", "code")


class DocumentType(CatalogTimestampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    allowed_extensions = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Extensiones separadas por coma, ej. pdf,docx",
    )

    class Meta:
        verbose_name = "Tipo documental"
        verbose_name_plural = "Tipos documentales"
        ordering = ("code",)


class Provider(CatalogTimestampedModel):
    legal_name = models.CharField(max_length=255)
    ruc = models.CharField(max_length=11)
    phone = models.CharField(max_length=30, blank=True, default="")
    main_contact = models.CharField(max_length=255)
    email = models.EmailField()
    website = models.URLField(blank=True, default="")
    address = models.TextField(blank=True, default="")
    service_types = models.ManyToManyField(ServiceType, related_name="providers", blank=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ("code",)


class Responsible(CatalogTimestampedModel):
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    job_title = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, default="")
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="responsibles")

    class Meta:
        verbose_name = "Responsable"
        verbose_name_plural = "Responsables"
        ordering = ("code",)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
