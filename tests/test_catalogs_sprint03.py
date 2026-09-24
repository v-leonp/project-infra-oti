import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.administration.constants import ROLE_ADMINISTRADOR, ROLE_USUARIO
from apps.administration.models import AuditLog
from apps.administration.role_setup import ensure_system_groups, setup_roles_and_permissions
from apps.catalogs.models import ODS, Provider, ServiceType

User = get_user_model()


@pytest.fixture
def roles(db):
    setup_roles_and_permissions()
    return ensure_system_groups()


@pytest.fixture
def admin_user(db, roles):
    user = User.objects.create_user("admin.cat", "admin@cat.local", "AdminCat123!")
    user.groups.add(roles[ROLE_ADMINISTRADOR])
    return user


@pytest.fixture
def regular_user(db, roles):
    user = User.objects.create_user("user.cat", "user@cat.local", "UserCat123!")
    user.groups.add(roles[ROLE_USUARIO])
    return user


@pytest.fixture
def admin_client(admin_user):
    client = Client()
    client.login(username="admin.cat", password="AdminCat123!")
    return client


@pytest.fixture
def user_client(regular_user):
    client = Client()
    client.login(username="user.cat", password="UserCat123!")
    return client


@pytest.mark.django_db
class TestCatalogAccess:
    def test_admin_can_access_catalogs(self, admin_client):
        assert admin_client.get(reverse("catalogs:ods_oes_list")).status_code == 200
        assert admin_client.get(reverse("catalogs:provider_list")).status_code == 200

    def test_user_forbidden(self, user_client):
        assert user_client.get(reverse("catalogs:ods_oes_list")).status_code == 403

    def test_menu_hidden_for_user(self, user_client):
        html = user_client.get(reverse("accounts:welcome")).content.decode()
        assert "Catálogos" not in html

    def test_htmx_forbidden(self, user_client):
        response = user_client.get(reverse("catalogs:sedes_list"), HTTP_HX_REQUEST="true")
        assert response.status_code == 403


@pytest.mark.django_db
class TestCatalogCRUD:
    def test_create_ods(self, admin_client, admin_user):
        response = admin_client.post(
            reverse("catalogs:ods_create"),
            data={
                "code": "ODS-01",
                "name": "Fin de la pobreza",
                "description": "Desc",
                "is_active": True,
            },
        )
        assert response.status_code == 302
        assert ODS.objects.filter(code="ODS-01").exists()
        assert AuditLog.objects.filter(action="catalog_created").exists()

    def test_duplicate_code_rejected(self, admin_client, admin_user):
        ODS.objects.create(
            code="ODS-99",
            name="Uno",
            description="",
            created_by=admin_user,
            updated_by=admin_user,
        )
        response = admin_client.post(
            reverse("catalogs:ods_create"),
            data={"code": "ods-99", "name": "Otro", "description": "", "is_active": True},
        )
        assert response.status_code == 200
        assert "código" in response.content.decode().lower()

    def test_provider_ruc_validation(self, admin_client, admin_user):
        st = ServiceType.objects.create(
            code="TS-01",
            name="Soporte",
            description="",
            created_by=admin_user,
            updated_by=admin_user,
        )
        response = admin_client.post(
            reverse("catalogs:provider_create"),
            data={
                "code": "PROV-01",
                "legal_name": "Proveedor Demo SAC",
                "ruc": "123",
                "service_types": [st.pk],
                "main_contact": "Ana Torres",
                "email": "ana@demo.local",
                "is_active": True,
            },
        )
        assert response.status_code == 200
        assert "11 dígitos" in response.content.decode()

    def test_provider_create_with_services(self, admin_client, admin_user):
        st = ServiceType.objects.create(
            code="TS-02",
            name="Mantenimiento",
            description="",
            created_by=admin_user,
            updated_by=admin_user,
        )
        response = admin_client.post(
            reverse("catalogs:provider_create"),
            data={
                "code": "PROV-02",
                "legal_name": "Soluciones Tech",
                "ruc": "12345678901",
                "service_types": [st.pk],
                "main_contact": "Luis Pérez",
                "email": "luis@demo.local",
                "is_active": True,
            },
        )
        assert response.status_code == 302
        provider = Provider.objects.get(code="PROV-02")
        assert provider.service_types.count() == 1

    def test_deactivate_service_type_blocked(self, admin_client, admin_user):
        st = ServiceType.objects.create(
            code="TS-03",
            name="Redes",
            description="",
            created_by=admin_user,
            updated_by=admin_user,
        )
        provider = Provider.objects.create(
            code="P-1",
            legal_name="P",
            ruc="10987654321",
            main_contact="C",
            email="c@x.local",
            created_by=admin_user,
            updated_by=admin_user,
        )
        provider.service_types.add(st)
        response = admin_client.post(
            reverse("catalogs:tipos_servicio_state", kwargs={"pk": st.pk}),
            data={"confirm": True, "state_action": "deactivate"},
        )
        assert response.status_code == 200
        assert "proveedores activos" in response.content.decode().lower()

    def test_search_case_insensitive(self, admin_client, admin_user):
        ODS.objects.create(
            code="ODS-SEARCH",
            name="Educación",
            description="",
            created_by=admin_user,
            updated_by=admin_user,
        )
        url = reverse("catalogs:ods_oes_list")
        response = admin_client.get(url, {"tab": "ods", "q": "educación"})
        assert "Educación" in response.content.decode()
