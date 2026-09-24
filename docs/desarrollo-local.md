# Desarrollo local — Infraestructura OTI

Este proyecto se trabaja **solo en entorno local** por ahora: sin despliegue, sin SMTP institucional ni servicios en la nube. Todo lo necesario corre en su máquina (`localhost`).

## Alcance local actual

| Área | Configuración local |
| ---- | ------------------- |
| Base de datos | **SQLite** (`db.sqlite3` en la raíz del repo) |
| Servidor web | `manage.py runserver` (solo desarrollo) |
| Correo | Backend de **consola** (los enlaces de recuperación se imprimen en la terminal) |
| Archivos estáticos | Carpeta `static/`; CSS generado con Node/Tailwind |
| Secretos | Archivo `.env` (no se sube a Git) |

PostgreSQL y SMTP quedan **documentados y preparados** en variables de entorno para una fase posterior; no son obligatorios hoy.

## Requisitos en su equipo

- **Python 3.12 – 3.14** (Django 5.2 no funciona con 3.9/3.10 antiguos del sistema)
- **Node.js 20+** (compilar Tailwind)
- Opcional: [uv](https://docs.astral.sh/uv/) para instalar Python 3.12 sin tocar el sistema

## Primera vez — configuración

Desde la raíz del repositorio:

```bash
cp .env.example .env
```

El `.env.example` ya trae valores pensados para local (`USE_SQLITE=True`, `DEBUG=True`, cookies sin `Secure`).

### Python y dependencias

**Opción A — uv (recomendada si no tiene Python 3.12 instalado):**

```bash
uv python install 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

**Opción B — venv clásico:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Base de datos y usuario

```bash
python manage.py migrate
python manage.py createsuperuser
```

Use el usuario y contraseña que defina en el asistente; esas credenciales son **solo locales** y no se guardan en el repositorio.

### Estilos (Tailwind)

```bash
npm install
npm run build:css
```

Mientras edita plantillas o CSS fuente:

```bash
npm run watch:css
```

## Uso diario

```bash
source .venv/bin/activate
python manage.py runserver
```

| URL | Uso |
| --- | --- |
| http://127.0.0.1:8000/ | Redirige al login |
| http://127.0.0.1:8000/login/ | Inicio de sesión |
| http://127.0.0.1:8000/inicio/ | Página protegida (tras login) |
| http://127.0.0.1:8000/password-reset/ | Recuperación de contraseña |
| http://127.0.0.1:8000/admin/ | Admin Django (superusuario) |

### Recuperación de contraseña en local

1. En `/password-reset/` ingrese el **correo** del usuario (debe existir en el admin, p. ej. el del `createsuperuser`).
2. Revise la **terminal** donde corre `runserver`: ahí aparece el cuerpo del correo con el enlace de restablecimiento.
3. Abra el enlace en el navegador y defina la nueva contraseña.

## Pruebas automatizadas

```bash
source .venv/bin/activate
pytest
```

`tests/conftest.py` fuerza `USE_SQLITE=True` para que las pruebas no dependan de PostgreSQL.

## Calidad de código

```bash
ruff check .
```

## Archivos que no se versionan

- `.env` — secretos y ajustes personales
- `.venv/` — entorno virtual
- `node_modules/` — dependencias npm
- `db.sqlite3` — base de datos local (se regenera con `migrate`)
- `staticfiles/` — salida de `collectstatic` (cuando se use)

## Cuando quiera pasar a PostgreSQL en local (futuro)

1. Levantar Postgres (p. ej. `docker compose up -d` usando el `docker-compose.yml` del repo).
2. En `.env`: `USE_SQLITE=False` y `DATABASE_URL=postgres://oti_user:oti_password@localhost:5432/infraestructura_oti`.
3. `python manage.py migrate`.

Hasta entonces, mantenga `USE_SQLITE=True`.

## Referencias

- [README.md](../README.md) — resumen del proyecto
- [sprint-01-login.md](sprint-01-login.md) — alcance y criterios del primer sprint
