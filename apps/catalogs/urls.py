from django.urls import path

from apps.catalogs import views

app_name = "catalogs"

urlpatterns = [
    path("ods-oes/", views.ODSOESListView.as_view(), name="ods_oes_list"),
    path("ods/nuevo/", views.ODSCreateEditView.as_view(), name="ods_create"),
    path("ods/<int:pk>/editar/", views.ODSCreateEditView.as_view(), name="ods_edit"),
    path("ods/<int:pk>/estado/", views.CatalogStateView.as_view(), {"catalog_key": "ods"}, name="ods_state"),
    path("oes/nuevo/", views.OESCreateEditView.as_view(), name="oes_create"),
    path("oes/<int:pk>/editar/", views.OESCreateEditView.as_view(), name="oes_edit"),
    path("oes/<int:pk>/estado/", views.CatalogStateView.as_view(), {"catalog_key": "oes"}, name="oes_state"),
    path("sedes/", views.GenericCatalogListView.as_view(catalog_key="sedes"), name="sedes_list"),
    path("sedes/nueva/", views.SiteCreateEditView.as_view(), name="sedes_create"),
    path("sedes/<int:pk>/editar/", views.SiteCreateEditView.as_view(), name="sedes_edit"),
    path(
        "sedes/<int:pk>/estado/",
        views.CatalogStateView.as_view(),
        {"catalog_key": "sedes"},
        name="sedes_state",
    ),
    path("proveedores/", views.ProviderListView.as_view(), name="provider_list"),
    path("proveedores/nuevo/", views.ProviderFormView.as_view(), name="provider_create"),
    path("proveedores/<int:pk>/detalle/", views.ProviderDetailView.as_view(), name="provider_detail"),
    path("proveedores/<int:pk>/editar/", views.ProviderFormView.as_view(), name="provider_edit"),
    path("proveedores/<int:pk>/estado/", views.ProviderStateView.as_view(), name="provider_state"),
    path("estados/", views.GenericCatalogListView.as_view(catalog_key="estados"), name="estados_list"),
    path("estados/nuevo/", views.StatusCreateEditView.as_view(), name="estados_create"),
    path("estados/<int:pk>/editar/", views.StatusCreateEditView.as_view(), name="estados_edit"),
    path(
        "estados/<int:pk>/estado/",
        views.CatalogStateView.as_view(),
        {"catalog_key": "estados"},
        name="estados_state",
    ),
    path(
        "tipos-servicio/",
        views.GenericCatalogListView.as_view(catalog_key="tipos-servicio"),
        name="tipos_servicio_list",
    ),
    path("tipos-servicio/nuevo/", views.ServiceTypeCreateEditView.as_view(), name="tipos_servicio_create"),
    path(
        "tipos-servicio/<int:pk>/editar/",
        views.ServiceTypeCreateEditView.as_view(),
        name="tipos_servicio_edit",
    ),
    path(
        "tipos-servicio/<int:pk>/estado/",
        views.CatalogStateView.as_view(),
        {"catalog_key": "tipos-servicio"},
        name="tipos_servicio_state",
    ),
    path(
        "responsables/",
        views.GenericCatalogListView.as_view(catalog_key="responsables"),
        name="responsables_list",
    ),
    path("responsables/nuevo/", views.ResponsibleCreateEditView.as_view(), name="responsables_create"),
    path(
        "responsables/<int:pk>/editar/",
        views.ResponsibleCreateEditView.as_view(),
        name="responsables_edit",
    ),
    path(
        "responsables/<int:pk>/estado/",
        views.CatalogStateView.as_view(),
        {"catalog_key": "responsables"},
        name="responsables_state",
    ),
    path(
        "tipos-documentales/",
        views.GenericCatalogListView.as_view(catalog_key="tipos-documentales"),
        name="tipos_documentales_list",
    ),
    path(
        "tipos-documentales/nuevo/",
        views.DocumentTypeCreateEditView.as_view(),
        name="tipos_documentales_create",
    ),
    path(
        "tipos-documentales/<int:pk>/editar/",
        views.DocumentTypeCreateEditView.as_view(),
        name="tipos_documentales_edit",
    ),
    path(
        "tipos-documentales/<int:pk>/estado/",
        views.CatalogStateView.as_view(),
        {"catalog_key": "tipos-documentales"},
        name="tipos_documentales_state",
    ),
]
