# Sprint 04 — Gestión de servicios de Internet

## Objetivo

Registrar, consultar y dar seguimiento técnico a servicios de Internet de las ODS/OES, con contratos, entregables, incidencias, documentos y reportes.

## Alcance

- Módulo `/internet/` (app `apps.internet`).
- Acceso **exclusivo** del grupo **Usuario** (sin superusuario ni Administrador).
- UI alineada al panel institucional (sidebar, KPIs, listados HTMX).

## Historias de usuario

| ID | Historia |
|----|----------|
| HU-04-01 | Gestionar servicios de Internet |
| HU-04-02 | Consultar vigencias e indicadores |
| HU-04-03 | Gestionar contratos y entregables |
| HU-04-04 | Gestionar incidencias |
| HU-04-05 | Documentos y reportes |

## Matriz de acceso

| Rol | Internet |
|-----|----------|
| Usuario | Permitido (403 si no pertenece al grupo) |
| Administrador | 403 |
| Superusuario | 403 |

## Rutas

- `/internet/servicios/` — listado, filtros, KPIs
- `/internet/servicios/nuevo/` — alta
- `/internet/servicios/<id>/` — ficha
- `/internet/servicios/<id>/editar/` — edición
- `/internet/servicios/<id>/estado/` — cambio de estado
- `/internet/contratos/`, `/entregables/`, `/incidencias/`, `/documentos/`, `/reportes/`

## Reglas de negocio destacadas

- **Próximo a vencer:** `INTERNET_SERVICE_EXPIRY_WARNING_DAYS` (default 30).
- Estados calculados: activo, próximo a vencer, vencido; más inactivo y con observaciones.
- Sin eliminación física de servicios/incidencias cerradas; archivado lógico.
- Documentos en `private_media/`; descarga solo autenticada (rol Usuario).

## Migraciones

- `internet.0001_initial`

## Pruebas

`tests/test_internet_sprint04.py` — acceso, CRUD, validaciones, documentos, CSRF, consultas.

## Ejecución manual

1. Usuario con grupo **Usuario** (no administrador).
2. `USE_SQLITE=True python manage.py runserver`
3. Login → menú **Internet** → **Servicios**.

## Definición de terminado

- [x] 71 pruebas en suite total
- [x] `manage.py check` sin errores
- [x] Sin migraciones pendientes
- [x] Tailwind compila
- [x] Solo rol Usuario accede al módulo
