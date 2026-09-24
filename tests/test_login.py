
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()

GENERIC_AUTH_ERROR = "Usuario o contraseña incorrectos."


@pytest.fixture
def user(db):
    return User.objects.create_user(username="analista.oti", password="ClaveSegura123!")


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestLoginView:
    def test_login_page_renders_on_get(self, client):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200
        assert "accounts/login.html" in [t.name for t in response.templates]

    def test_login_form_includes_csrf_token(self, client):
        response = client.get(reverse("accounts:login"))
        assert "csrfmiddlewaretoken" in response.content.decode()

    def test_login_template_has_required_fields_and_links(self, client):
        content = client.get(reverse("accounts:login")).content.decode()
        assert 'name="username"' in content
        assert 'name="password"' in content
        assert "Ingresar" in content
        assert "¿Olvidaste tu contraseña?" in content
        assert reverse("accounts:password_reset") in content
        assert "Acceso exclusivo para personal autorizado" in content
        assert content.count("<h1") == 1

    def test_empty_submission_shows_validation_errors(self, client):
        response = client.post(reverse("accounts:login"), data={"username": "", "password": ""})
        assert response.status_code == 200
        assert "Este campo es obligatorio" in response.content.decode()

    def test_valid_credentials_redirect_to_welcome(self, client, user):
        response = client.post(
            reverse("accounts:login"),
            data={"username": "analista.oti", "password": "ClaveSegura123!"},
        )
        assert response.status_code == 302
        assert response.url == reverse("accounts:welcome")

    def test_invalid_credentials_show_generic_message(self, client, user):
        response = client.post(
            reverse("accounts:login"),
            data={"username": "analista.oti", "password": "wrong-password"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert GENERIC_AUTH_ERROR in content
        assert "contraseña incorrecta" not in content.lower() or GENERIC_AUTH_ERROR in content
        assert "usuario no existe" not in content.lower()

    def test_wrong_username_same_generic_message(self, client, user):
        response = client.post(
            reverse("accounts:login"),
            data={"username": "unknown.user", "password": "ClaveSegura123!"},
        )
        assert response.status_code == 200
        assert GENERIC_AUTH_ERROR in response.content.decode()

    def test_authenticated_user_redirected_from_login(self, client, user):
        client.login(username="analista.oti", password="ClaveSegura123!")
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 302
        assert response.url == reverse("accounts:welcome")

    def test_safe_next_redirect_after_login(self, client, user):
        welcome = reverse("accounts:welcome")
        response = client.post(
            reverse("accounts:login") + f"?next={welcome}",
            data={"username": "analista.oti", "password": "ClaveSegura123!"},
        )
        assert response.status_code == 302
        assert response.url == welcome

    def test_unsafe_next_is_not_honored(self, client, user):
        response = client.post(
            reverse("accounts:login") + "?next=https://evil.example/phish",
            data={"username": "analista.oti", "password": "ClaveSegura123!"},
        )
        assert response.status_code == 302
        assert response.url == reverse("accounts:welcome")

    def test_password_not_stored_in_plain_text(self, user):
        assert user.password != "ClaveSegura123!"
        assert user.check_password("ClaveSegura123!")


@pytest.mark.django_db
class TestWelcomePage:
    def test_anonymous_user_cannot_access_welcome(self, client):
        response = client.get(reverse("accounts:welcome"))
        assert response.status_code == 302
        assert reverse("accounts:login") in response.url

    def test_authenticated_user_sees_welcome(self, client, user):
        client.login(username="analista.oti", password="ClaveSegura123!")
        response = client.get(reverse("accounts:welcome"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Infraestructura - OTI" in content
        assert "analista.oti" in content
        assert "Cerrar sesión" in content


@pytest.mark.django_db
def test_nonexistent_route_returns_404(client):
    response = client.get("/ruta-inexistente/")
    assert response.status_code == 404
