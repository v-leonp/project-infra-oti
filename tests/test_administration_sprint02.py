import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.administration.constants import ROLE_ADMINISTRADOR, ROLE_USUARIO
from apps.administration.models import AuditLog
from apps.administration.role_setup import ensure_system_groups, setup_roles_and_permissions

User = get_user_model()


@pytest.fixture
def roles(db):
    setup_roles_and_permissions()
    return ensure_system_groups()


@pytest.fixture
def admin_user(db, roles):
    user = User.objects.create_user(
        username="admin.oti",
        email="admin@oti.local",
        password="AdminSegura123!",
        first_name="Admin",
        last_name="OTI",
    )
    user.groups.add(roles[ROLE_ADMINISTRADOR])
    return user


@pytest.fixture
def regular_user(db, roles):
    user = User.objects.create_user(
        username="usuario.oti",
        email="usuario@oti.local",
        password="UsuarioSegura123!",
        first_name="Usuario",
        last_name="Demo",
    )
    user.groups.add(roles[ROLE_USUARIO])
    return user


@pytest.fixture
def admin_client(admin_user):
    client = Client()
    client.login(username="admin.oti", password="AdminSegura123!")
    return client


@pytest.fixture
def user_client(regular_user):
    client = Client()
    client.login(username="usuario.oti", password="UsuarioSegura123!")
    return client


@pytest.mark.django_db
class TestAccessControl:
    def test_admin_can_access_user_list(self, admin_client):
        response = admin_client.get(reverse("administration:user_list"))
        assert response.status_code == 200

    def test_superuser_can_access_user_list(self, db, roles):
        User.objects.create_superuser("root", "root@local", "RootSegura123!")
        client = Client()
        client.login(username="root", password="RootSegura123!")
        assert client.get(reverse("administration:user_list")).status_code == 200

    def test_regular_user_gets_403_on_admin_urls(self, user_client):
        urls = [
            reverse("administration:user_list"),
            reverse("administration:user_create"),
            reverse("administration:group_permissions"),
            reverse("administration:audit_list"),
        ]
        for url in urls:
            assert user_client.get(url).status_code == 403

    def test_regular_user_menu_hides_administration_links(self, user_client):
        content = user_client.get(reverse("accounts:welcome")).content.decode()
        assert "Usuarios" not in content
        assert "Grupos y permisos" not in content

    def test_htmx_user_list_requires_admin(self, user_client):
        response = user_client.get(
            reverse("administration:user_list"),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestUserManagement:
    def test_create_user_valid(self, admin_client, roles):
        response = admin_client.post(
            reverse("administration:user_create"),
            data={
                "username": "nuevo.user",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "email": "nuevo@oti.local",
                "role": ROLE_USUARIO,
                "password1": "NuevaClave123!",
                "password2": "NuevaClave123!",
                "is_active": True,
            },
        )
        assert response.status_code == 302
        created = User.objects.get(username="nuevo.user")
        assert created.check_password("NuevaClave123!")
        assert created.groups.filter(name=ROLE_USUARIO).exists()
        assert AuditLog.objects.filter(action="user_created", target_user=created).exists()

    def test_duplicate_username_rejected(self, admin_client, regular_user):
        response = admin_client.post(
            reverse("administration:user_create"),
            data={
                "username": regular_user.username,
                "first_name": "X",
                "last_name": "Y",
                "email": "otro@oti.local",
                "role": ROLE_USUARIO,
                "password1": "NuevaClave123!",
                "password2": "NuevaClave123!",
            },
        )
        assert response.status_code == 200
        assert "ya está en uso" in response.content.decode()

    def test_duplicate_email_rejected(self, admin_client, regular_user):
        response = admin_client.post(
            reverse("administration:user_create"),
            data={
                "username": "otro.user",
                "first_name": "X",
                "last_name": "Y",
                "email": regular_user.email,
                "role": ROLE_USUARIO,
                "password1": "NuevaClave123!",
                "password2": "NuevaClave123!",
            },
        )
        assert response.status_code == 200
        assert "correo" in response.content.decode().lower()

    def test_search_users(self, admin_client, admin_user, regular_user):
        response = admin_client.get(reverse("administration:user_list"), {"q": "usuario.oti"})
        assert response.status_code == 200
        assert "usuario.oti" in response.content.decode()

    def test_filter_by_role(self, admin_client, admin_user, regular_user):
        response = admin_client.get(reverse("administration:user_list"), {"role": ROLE_USUARIO})
        content = response.content.decode()
        assert "usuario.oti" in content

    def test_deactivate_user_post_only_flow(self, admin_client, regular_user):
        url = reverse("administration:user_state", kwargs={"pk": regular_user.pk})
        assert admin_client.get(f"{url}?action=deactivate").status_code == 200
        response = admin_client.post(
            url,
            data={"confirm": True, "state_action": "deactivate"},
        )
        assert response.status_code == 302
        regular_user.refresh_from_db()
        assert regular_user.is_active is False

    def test_admin_cannot_deactivate_self(self, admin_client, admin_user):
        url = reverse("administration:user_state", kwargs={"pk": admin_user.pk})
        response = admin_client.post(
            url,
            data={"confirm": True, "state_action": "deactivate"},
        )
        assert response.status_code == 200
        assert "propia cuenta" in response.content.decode().lower()

    def test_cannot_deactivate_last_admin(self, admin_client, admin_user):
        # Attempt role demotion via edit (only one active administrator exists)
        response = admin_client.post(
            reverse("administration:user_edit", kwargs={"pk": admin_user.pk}),
            data={
                "first_name": admin_user.first_name,
                "last_name": admin_user.last_name,
                "email": admin_user.email,
                "role": ROLE_USUARIO,
                "is_active": True,
            },
        )
        assert response.status_code == 200
        assert "último" in response.content.decode().lower()

    def test_audit_does_not_store_plain_password(self, admin_client, roles):
        admin_client.post(
            reverse("administration:user_create"),
            data={
                "username": "audit.user",
                "first_name": "Audit",
                "last_name": "User",
                "email": "audit@oti.local",
                "role": ROLE_USUARIO,
                "password1": "ClaveSecreta123!",
                "password2": "ClaveSecreta123!",
            },
        )
        log = AuditLog.objects.filter(target_user__username="audit.user").first()
        assert log is not None
        blob = str(log.old_values) + str(log.new_values)
        assert "ClaveSecreta123!" not in blob
        assert "password" not in blob.lower() or "password_changed" in blob.lower()

    def test_csrf_required_on_create(self, admin_client, roles):
        client = Client(enforce_csrf_checks=True)
        client.login(username="admin.oti", password="AdminSegura123!")
        response = client.post(
            reverse("administration:user_create"),
            data={"username": "csrf.test"},
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestGroupsAndAudit:
    def test_group_permissions_page(self, admin_client):
        response = admin_client.get(reverse("administration:group_permissions"))
        assert response.status_code == 200
        assert "Permisos del sistema" in response.content.decode()

    def test_audit_list_read_only(self, admin_client, admin_user):
        AuditLog.objects.create(actor=admin_user, action="user_created", new_values={"demo": True})
        response = admin_client.get(reverse("administration:audit_list"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Creación de usuario" in content
        assert "admin.oti" in content
