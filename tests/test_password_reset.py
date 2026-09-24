import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestPasswordResetFlow:
    def test_password_reset_page_renders(self, client):
        response = client.get(reverse("accounts:password_reset"))
        assert response.status_code == 200
        assert "csrfmiddlewaretoken" in response.content.decode()

    def test_password_reset_does_not_reveal_unknown_email(self, client):
        response = client.post(
            reverse("accounts:password_reset"),
            data={"email": "noexiste@institucion.gov.co"},
        )
        assert response.status_code == 302
        assert response.url == reverse("accounts:password_reset_done")

    def test_password_reset_sends_mail_for_known_user(self, client):
        User.objects.create_user(
            username="analista.oti",
            email="analista@institucion.gov.co",
            password="ClaveSegura123!",
        )
        response = client.post(
            reverse("accounts:password_reset"),
            data={"email": "analista@institucion.gov.co"},
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 1

    def test_password_reset_done_page(self, client):
        response = client.get(reverse("accounts:password_reset_done"))
        assert response.status_code == 200
