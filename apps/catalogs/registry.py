from apps.catalogs import forms
from apps.catalogs.models import (
    ODS,
    OES,
    CatalogStatus,
    DocumentType,
    Responsible,
    ServiceType,
    Site,
)

CATALOG_CONFIG = {
    "ods": {
        "model": ODS,
        "label": "ODS",
        "title": "Objetivos de Desarrollo Sostenible",
        "form_class": forms.ODSForm,
        "search_fields": ("code", "name", "description"),
        "list_columns": ("code", "name", "description"),
    },
    "oes": {
        "model": OES,
        "label": "OES",
        "title": "Objetivos Estratégicos del Sector",
        "form_class": forms.OESForm,
        "search_fields": ("code", "name", "description"),
        "list_columns": ("code", "name", "description"),
    },
    "sedes": {
        "model": Site,
        "label": "Sedes",
        "title": "Sedes",
        "form_class": forms.SiteForm,
        "search_fields": ("code", "name", "address", "district", "province", "department"),
        "list_columns": ("code", "name", "department", "province"),
    },
    "estados": {
        "model": CatalogStatus,
        "label": "Estados",
        "title": "Estados del sistema",
        "form_class": forms.CatalogStatusForm,
        "search_fields": ("code", "name", "description"),
        "list_columns": ("code", "name", "sort_order"),
    },
    "tipos-servicio": {
        "model": ServiceType,
        "label": "Tipos de servicio",
        "title": "Tipos de servicio",
        "form_class": forms.ServiceTypeForm,
        "search_fields": ("code", "name", "description"),
        "list_columns": ("code", "name", "description"),
    },
    "tipos-documentales": {
        "model": DocumentType,
        "label": "Tipos documentales",
        "title": "Tipos documentales",
        "form_class": forms.DocumentTypeForm,
        "search_fields": ("code", "name", "description"),
        "list_columns": ("code", "name", "description"),
    },
    "responsables": {
        "model": Responsible,
        "label": "Responsables",
        "title": "Responsables",
        "form_class": forms.ResponsibleForm,
        "search_fields": ("code", "first_name", "last_name", "email", "job_title"),
        "list_columns": ("code", "first_name", "last_name", "job_title"),
    },
}

PROVIDER_KEY = "proveedores"
