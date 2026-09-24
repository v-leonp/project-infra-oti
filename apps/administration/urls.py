from django.urls import path

from apps.administration import views

app_name = "administration"

urlpatterns = [
    path("usuarios/", views.UserListView.as_view(), name="user_list"),
    path("usuarios/nuevo/", views.UserCreateView.as_view(), name="user_create"),
    path("usuarios/<int:pk>/detalle/", views.UserDetailView.as_view(), name="user_detail"),
    path("usuarios/<int:pk>/editar/", views.UserUpdateView.as_view(), name="user_edit"),
    path("usuarios/<int:pk>/estado/", views.UserStateChangeView.as_view(), name="user_state"),
    path("grupos-permisos/", views.GroupPermissionsView.as_view(), name="group_permissions"),
    path("auditoria/", views.AuditLogListView.as_view(), name="audit_list"),
]
