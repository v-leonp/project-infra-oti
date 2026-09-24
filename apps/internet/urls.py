from django.urls import path

from apps.internet import views

app_name = "internet"

urlpatterns = [
    path("servicios/", views.ServiceListView.as_view(), name="service_list"),
    path("servicios/nuevo/", views.ServiceCreateView.as_view(), name="service_create"),
    path("servicios/<int:pk>/", views.ServiceDetailView.as_view(), name="service_detail"),
    path("servicios/<int:pk>/editar/", views.ServiceUpdateView.as_view(), name="service_edit"),
    path("servicios/<int:pk>/estado/", views.ServiceStateView.as_view(), name="service_state"),
    path("contratos/", views.ContractListView.as_view(), name="contract_list"),
    path("contratos/nuevo/", views.ContractCreateView.as_view(), name="contract_create"),
    path("contratos/<int:pk>/editar/", views.ContractUpdateView.as_view(), name="contract_edit"),
    path("entregables/", views.DeliverableListView.as_view(), name="deliverable_list"),
    path("entregables/nuevo/", views.DeliverableCreateView.as_view(), name="deliverable_create"),
    path(
        "entregables/<int:pk>/editar/",
        views.DeliverableUpdateView.as_view(),
        name="deliverable_edit",
    ),
    path("incidencias/", views.IncidentListView.as_view(), name="incident_list"),
    path("incidencias/nueva/", views.IncidentCreateView.as_view(), name="incident_create"),
    path(
        "incidencias/<int:pk>/editar/",
        views.IncidentUpdateView.as_view(),
        name="incident_edit",
    ),
    path("documentos/", views.DocumentListView.as_view(), name="document_list"),
    path(
        "documentos/<int:pk>/descargar/",
        views.DocumentDownloadView.as_view(),
        name="document_download",
    ),
    path("reportes/", views.ReportView.as_view(), name="report_list"),
]
