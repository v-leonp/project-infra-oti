import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


@pytest.fixture
def authenticated_client(db):
    user = User.objects.create_user(username="analista.oti", password="ClaveSegura123!")
    client = Client()
    client.login(username=user.username, password="ClaveSegura123!")
    return client


@pytest.mark.django_db
class TestLogout:
    def test_logout_via_post_clears_session(self, authenticated_client):
        response = authenticated_client.post(reverse("accounts:logout"))
        assert response.status_code == 302
        assert response.url == reverse("accounts:login")

        follow = authenticated_client.get(reverse("accounts:welcome"))
        assert follow.status_code == 302

    def test_logout_get_not_allowed(self, authenticated_client):
        response = authenticated_client.get(reverse("accounts:logout"))
        assert response.status_code == 405
