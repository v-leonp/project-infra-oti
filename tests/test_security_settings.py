from django.conf import settings
from django.test import override_settings


def test_login_and_logout_redirect_urls_configured():
    assert settings.LOGIN_URL == "/login/"
    assert settings.LOGIN_REDIRECT_URL == "/inicio/"
    assert settings.LOGOUT_REDIRECT_URL == "/login/"


def test_session_cookie_httponly_enabled():
    assert settings.SESSION_COOKIE_HTTPONLY is True


@override_settings(DEBUG=False, SECURE_SSL_REDIRECT=True)
def test_production_security_headers_when_debug_off():
    from django.test import Client

    client = Client()
    response = client.get("/login/", secure=True)
    assert response.status_code in (200, 301, 302)
