INTERNET_PAGE_SIZE = 5

SERVICE_STATUS_ACTIVE = "active"
SERVICE_STATUS_EXPIRING = "expiring"
SERVICE_STATUS_OBSERVATIONS = "observations"
SERVICE_STATUS_EXPIRED = "expired"
SERVICE_STATUS_INACTIVE = "inactive"

SERVICE_STATUS_LABELS = {
    SERVICE_STATUS_ACTIVE: "Activo",
    SERVICE_STATUS_EXPIRING: "Próximo a vencer",
    SERVICE_STATUS_OBSERVATIONS: "Con observaciones",
    SERVICE_STATUS_EXPIRED: "Vencido",
    SERVICE_STATUS_INACTIVE: "Inactivo",
}

SERVICE_STATUS_FILTER_CHOICES = [
    ("", "Todos los estados"),
    (SERVICE_STATUS_ACTIVE, SERVICE_STATUS_LABELS[SERVICE_STATUS_ACTIVE]),
    (SERVICE_STATUS_EXPIRING, SERVICE_STATUS_LABELS[SERVICE_STATUS_EXPIRING]),
    (SERVICE_STATUS_OBSERVATIONS, SERVICE_STATUS_LABELS[SERVICE_STATUS_OBSERVATIONS]),
    (SERVICE_STATUS_EXPIRED, SERVICE_STATUS_LABELS[SERVICE_STATUS_EXPIRED]),
    (SERVICE_STATUS_INACTIVE, SERVICE_STATUS_LABELS[SERVICE_STATUS_INACTIVE]),
]

LINK_TYPE_FIBER = "fibra_optica"
LINK_TYPE_RADIO = "radioenlace"
LINK_TYPE_COPPER = "cobre"
LINK_TYPE_SATELLITE = "satelite"
LINK_TYPE_OTHER = "otro"

LINK_TYPE_CHOICES = [
    (LINK_TYPE_FIBER, "Fibra óptica"),
    (LINK_TYPE_RADIO, "Radioenlace"),
    (LINK_TYPE_COPPER, "Cobre"),
    (LINK_TYPE_SATELLITE, "Satélite"),
    (LINK_TYPE_OTHER, "Otro"),
]

CONTRACT_STATUS_ACTIVE = "active"
CONTRACT_STATUS_EXPIRED = "expired"
CONTRACT_STATUS_INACTIVE = "inactive"

CONTRACT_STATUS_CHOICES = [
    (CONTRACT_STATUS_ACTIVE, "Vigente"),
    (CONTRACT_STATUS_EXPIRED, "Vencido"),
    (CONTRACT_STATUS_INACTIVE, "Inactivo"),
]

DELIVERABLE_STATUS_PENDING = "pending"
DELIVERABLE_STATUS_SUBMITTED = "submitted"
DELIVERABLE_STATUS_OBSERVED = "observed"
DELIVERABLE_STATUS_REMEDIED = "remedied"
DELIVERABLE_STATUS_APPROVED = "approved"
DELIVERABLE_STATUS_LATE = "late"

DELIVERABLE_STATUS_CHOICES = [
    (DELIVERABLE_STATUS_PENDING, "Pendiente"),
    (DELIVERABLE_STATUS_SUBMITTED, "Presentado"),
    (DELIVERABLE_STATUS_OBSERVED, "Observado"),
    (DELIVERABLE_STATUS_REMEDIED, "Subsanado"),
    (DELIVERABLE_STATUS_APPROVED, "Aprobado"),
    (DELIVERABLE_STATUS_LATE, "Fuera de plazo"),
]

INCIDENT_STATUS_OPEN = "open"
INCIDENT_STATUS_CLOSED = "closed"

INCIDENT_STATUS_CHOICES = [
    (INCIDENT_STATUS_OPEN, "Abierta"),
    (INCIDENT_STATUS_CLOSED, "Cerrada"),
]

DOCUMENT_RELATED_SERVICE = "service"
DOCUMENT_RELATED_CONTRACT = "contract"
DOCUMENT_RELATED_DELIVERABLE = "deliverable"
DOCUMENT_RELATED_INCIDENT = "incident"

DOCUMENT_RELATED_CHOICES = [
    (DOCUMENT_RELATED_SERVICE, "Servicio"),
    (DOCUMENT_RELATED_CONTRACT, "Contrato"),
    (DOCUMENT_RELATED_DELIVERABLE, "Entregable"),
    (DOCUMENT_RELATED_INCIDENT, "Incidencia"),
]

DEFAULT_ALLOWED_DOCUMENT_EXTENSIONS = ("pdf", "doc", "docx", "xls", "xlsx", "png", "jpg", "jpeg")
BLOCKED_DOCUMENT_EXTENSIONS = frozenset(
    {"exe", "bat", "cmd", "com", "msi", "sh", "bash", "ps1", "js", "vbs", "scr", "dll"}
)

AUDIT_SERVICE_CREATED = "internet_service_created"
AUDIT_SERVICE_UPDATED = "internet_service_updated"
AUDIT_SERVICE_STATE_CHANGED = "internet_service_state_changed"
AUDIT_SERVICE_PROVIDER_CHANGED = "internet_service_provider_changed"
AUDIT_SERVICE_DATES_CHANGED = "internet_service_dates_changed"
AUDIT_CONTRACT_CREATED = "internet_contract_created"
AUDIT_CONTRACT_UPDATED = "internet_contract_updated"
AUDIT_DELIVERABLE_CREATED = "internet_deliverable_created"
AUDIT_DELIVERABLE_UPDATED = "internet_deliverable_updated"
AUDIT_DELIVERABLE_STATE = "internet_deliverable_state_changed"
AUDIT_INCIDENT_CREATED = "internet_incident_created"
AUDIT_INCIDENT_UPDATED = "internet_incident_updated"
AUDIT_INCIDENT_CLOSED = "internet_incident_closed"
AUDIT_DOCUMENT_UPLOADED = "internet_document_uploaded"
AUDIT_DOCUMENT_DOWNLOADED = "internet_document_downloaded"

AUDIT_INTERNET_ACTION_LABELS = {
    AUDIT_SERVICE_CREATED: "Creación de servicio de Internet",
    AUDIT_SERVICE_UPDATED: "Edición de servicio de Internet",
    AUDIT_SERVICE_STATE_CHANGED: "Cambio de estado de servicio",
    AUDIT_SERVICE_PROVIDER_CHANGED: "Cambio de proveedor de servicio",
    AUDIT_SERVICE_DATES_CHANGED: "Cambio de vigencia de servicio",
    AUDIT_CONTRACT_CREATED: "Creación de contrato",
    AUDIT_CONTRACT_UPDATED: "Edición de contrato",
    AUDIT_DELIVERABLE_CREATED: "Registro de entregable",
    AUDIT_DELIVERABLE_UPDATED: "Edición de entregable",
    AUDIT_DELIVERABLE_STATE: "Cambio de estado de entregable",
    AUDIT_INCIDENT_CREATED: "Registro de incidencia",
    AUDIT_INCIDENT_UPDATED: "Edición de incidencia",
    AUDIT_INCIDENT_CLOSED: "Cierre de incidencia",
    AUDIT_DOCUMENT_UPLOADED: "Carga de documento",
    AUDIT_DOCUMENT_DOWNLOADED: "Descarga de documento",
}
