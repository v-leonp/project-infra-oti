from django.conf import settings
from django.db import models

from apps.administration.permissions_registry import build_custom_permissions


class AccessControlMeta(models.Model):
    """Modelo ancla para permisos personalizados por módulo funcional."""

    class Meta:
        verbose_name = "Metadatos de control de acceso"
        verbose_name_plural = "Metadatos de control de acceso"
        permissions = build_custom_permissions()


class GroupProfile(models.Model):
    group = models.OneToOneField("auth.Group", on_delete=models.CASCADE, related_name="profile")
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Perfil de grupo"
        verbose_name_plural = "Perfiles de grupo"

    def __str__(self) -> str:
        return f"Perfil: {self.group.name}"


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_actions_performed",
    )
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events_as_target",
    )
    target_group = models.ForeignKey(
        "auth.Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=64)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Registro de auditoría"
        verbose_name_plural = "Registros de auditoría"

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
