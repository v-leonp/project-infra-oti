# Infraestructura - OTI

Sistema web institucional para la gestión interna de servicios y activos tecnológicos (OTI).

**Fase actual:** desarrollo **100 % local** (SQLite, `runserver`, correo en consola). Sin despliegue ni integraciones externas por ahora.

**Sprint 01:** autenticación, login, recuperación de contraseña y página provisional `/inicio/`.

**Sprint 02:** administración de usuarios, roles, permisos y auditoría (`/administracion/`, solo Administrador).

**Sprint 03:** catálogos maestros (`/catalogos/`, solo Administrador).

**Sprint 04:** servicios de Internet (`/internet/`, solo grupo **Usuario**).

## Documentación

| Documento | Contenido |
| --------- | --------- |
| **[docs/desarrollo-local.md](docs/desarrollo-local.md)** | Guía completa: requisitos, primera vez, uso diario, pruebas, recuperación de contraseña |
| [docs/sprint-01-login.md](docs/sprint-01-login.md) | Historia de usuario, criterios de aceptación y TDD del sprint |
| [docs/sprint-02-usuarios-roles.md](docs/sprint-02-usuarios-roles.md) | Usuarios, roles, permisos y auditoría |
| [docs/sprint-03-catalogos.md](docs/sprint-03-catalogos.md) | Catálogos maestros |
| [docs/sprint-04-internet.md](docs/sprint-04-internet.md) | Servicios de Internet |

## Inicio rápido (local)

```bash
cp .env.example .env
uv python install 3.12 && uv venv --python 3.12 .venv   # o: python3.12 -m venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"   # o: pip install -e ".[dev]"
python manage.py migrate
python manage.py createsuperuser
npm install && npm run build:css
python manage.py runserver
```

Abra **http://127.0.0.1:8000/login/** e ingrese con el superusuario que creó.

Detalle de cada paso, correo de recuperación y archivos ignorados por Git: **[docs/desarrollo-local.md](docs/desarrollo-local.md)**.

## Stack (objetivo del proyecto)

| Componente | Uso en local hoy |
| ---------- | ---------------- |
| Python 3.12 – 3.14 | Backend |
| Django 5.2 LTS | Auth, plantillas, API futura |
| SQLite | Base de datos (`USE_SQLITE=True`) |
| PostgreSQL 18 | Opcional más adelante (`DATABASE_URL` + `docker-compose.yml`) |
| Tailwind CSS 3 | Estilos (`npm run build:css`) |
| pytest + pytest-django | Pruebas |

## Rutas

| Ruta | Descripción |
| ---- | ----------- |
| `/login/` | Inicio de sesión |
| `/logout/` | Cierre de sesión (POST) |
| `/password-reset/` | Recuperación de contraseña |
| `/inicio/` | Bienvenida (requiere sesión) |

## Pruebas

```bash
source .venv/bin/activate
pytest
```

## Estructura

```text
config/              # Settings y URLs Django
apps/accounts/       # Autenticación
templates/           # HTML (login, recuperación, bienvenida)
static/              # CSS, JS, imágenes
tests/               # pytest-django
docs/                # Documentación (local, sprints)
```

## Seguridad (recordatorio)

- `.env` no se commitea; use `.env.example` como plantilla.
- `runserver` es solo para desarrollo local.
- Cuando exista un entorno institucional: `DEBUG=False`, `SECRET_KEY` única, cookies seguras y SMTP real (variables comentadas en `.env.example`).
