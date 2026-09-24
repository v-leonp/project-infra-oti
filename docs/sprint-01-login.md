# Sprint 01: Autenticación y acceso inicial

## Objetivo

Entregar la base del monolito modular **Infraestructura - OTI** con autenticación segura, pantalla de login de alta fidelidad, cierre de sesión, recuperación de contraseña y página protegida provisional (`/inicio/`).

## Historia de usuario

**HU-01 – Inicio de sesión**

Como usuario autorizado de la Oficina de Tecnologías de la Información, quiero autenticarme mediante mi usuario y contraseña, para acceder de forma segura al sistema Infraestructura - OTI.

## Criterios de aceptación

1. Campos usuario y contraseña obligatorios.
2. Credenciales válidas → `/inicio/`.
3. Credenciales inválidas → mensaje genérico sin revelar qué dato falló.
4. Rutas protegidas exigen autenticación.
5. Usuario autenticado en `/login/` → redirección a `/inicio/`.
6. Mostrar/ocultar contraseña accesible.
7. Enlace a recuperación de contraseña.
8. Cierre de sesión por `POST`.
9. Interfaz responsiva y navegable por teclado.
10. CSRF en formularios de autenticación.
11. Contraseñas hasheadas (auth de Django).

## Entorno de trabajo

Todo el sprint se ejecuta en **máquina local** (sin despliegue). Guía operativa: [desarrollo-local.md](desarrollo-local.md).

## Tareas técnicas

- Proyecto Django 5.2 (`config/`) y app `apps.accounts`.
- **SQLite** por defecto (`USE_SQLITE=True`); PostgreSQL documentado para una fase posterior.
- Tailwind CSS compilado a `static/css/dist/main.css`.
- Plantillas del flujo de recuperación con identidad visual común.
- Variables en `.env` / `.env.example`.
- Suite `pytest` + `pytest-django`.

## Evidencia TDD (ciclo Red → Green → Refactor)

| Orden | Prueba (Red) | Implementación (Green) | Refactor |
| ----- | ------------ | ---------------------- | -------- |
| 1 | `test_login_page_renders_on_get` | `SecureLoginView` + `login.html` | Layout compartido `_auth_layout` |
| 2 | `test_login_form_includes_csrf_token` | Plantilla con `{% csrf_token %}` | — |
| 3 | `test_empty_submission_shows_validation_errors` | Campos requeridos en formulario y HTML | Mensajes por campo con `aria-*` |
| 4 | `test_valid_credentials_redirect_to_welcome` | `LoginView` + `WelcomeView` | `session.cycle_key()` tras login |
| 5 | `test_invalid_credentials_show_generic_message` | `LoginForm.error_messages` | Un solo mensaje institucional |
| 6 | `test_anonymous_user_cannot_access_welcome` | `LoginRequiredMixin` | URLs centralizadas en `accounts/urls.py` |
| 7 | `test_authenticated_user_redirected_from_login` | `redirect_authenticated_user = True` | — |
| 8 | `test_logout_via_post_clears_session` | `SecureLogoutView` solo POST | Formulario POST en bienvenida |
| 9 | `test_password_reset_*` | Vistas oficiales de Django + plantillas | Formulario de correo institucional |
| 10 | `test_safe_next_redirect_after_login` | Comportamiento estándar de `LoginView` | Prueba de URL externa rechazada |
| 11 | `test_production_security_headers_when_debug_off` | Bloque `if not DEBUG` en `settings.py` | — |

## Definition of Done

- [x] Login alineado con la referencia visual (dos columnas en escritorio).
- [x] Autenticación real con `django.contrib.auth`.
- [x] PostgreSQL configurado por entorno.
- [x] Pruebas automatizadas en verde.
- [x] Tailwind compilado sin errores.
- [x] Migraciones aplicables.
- [x] Sin secretos en el repositorio.
- [x] `README.md` con pasos de arranque.
