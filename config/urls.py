from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("administracion/", include("apps.administration.urls")),
    path("catalogos/", include("apps.catalogs.urls")),
    path("internet/", include("apps.internet.urls")),
    path("", include("apps.accounts.urls")),
]
