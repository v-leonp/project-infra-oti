# Sprint 02 — Usuarios, roles y permisos

## Objetivo

Módulo seguro de administración de usuarios, roles (grupos Django), permisos y auditoría, accesible solo para **Administrador** y **superusuarios**.

## Alcance

- Gestión de usuarios (listado, alta, edición, detalle, activar/desactivar).
- Grupos **Administrador** y **Usuario** con matriz de permisos.
- Auditoría de solo lectura.
- UI tipo panel (sidebar + topbar) alineada a la referencia visual.
- HTMX en listados (usuarios y auditoría) con fallback sin JavaScript.

Fuera de alcance: Configuración, eliminación física, roles extra (Operador, Supervisor, Consultor).

## Historias de usuario

### HU-02-01 — Gestionar usuarios

Como Administrador, quiero registrar y administrar usuarios para controlar quién puede utilizar el sistema.

### HU-02-02 — Gestionar roles y permisos

Como Administrador, quiero asignar roles y permisos para controlar las funcionalidades disponibles.

### HU-02-03 — Consultar auditoría

Como Administrador, quiero consultar la trazabilidad de las operaciones.

## Reglas de negocio

1. Solo **Administrador** (grupo) o **superusuario** accede a `/administracion/*` (403 para **Usuario**).
2. Un usuario tiene un solo rol/grupo: Administrador o Usuario.
3. No hay borrado físico; solo activar/desactivar (POST + confirmación).
4. Un administrador no puede desactivarse a sí mismo.
5. No se puede desactivar ni degradar al último Administrador activo.
6. El grupo **Usuario** no puede recibir permisos de módulos protegidos (`usuarios`, `grupos_permisos`, `auditoria`, `administracion`).
7. La auditoría no almacena contraseñas ni secretos.

## Matriz de permisos

Definida en `apps/administration/permissions_registry.py` (módulos × acciones: ver, crear, editar, cambiar estado). Los codenames se almacenan en permisos Django asociados a `AccessControlMeta`.

## Modelo de datos

| Modelo | Uso |
| ------ | --- |
| `AccessControlMeta` | Ancla de permisos personalizados |
| `GroupProfile` | Descripción del grupo |
| `AuditLog` | Trazabilidad (actor, objetivo, JSON antes/después, IP, fecha) |

## Rutas

| Ruta | Nombre |
| ---- | ------ |
| `/administracion/usuarios/` | Listado |
| `/administracion/usuarios/nuevo/` | Alta |
| `/administracion/usuarios/<pk>/detalle/` | Detalle |
| `/administracion/usuarios/<pk>/editar/` | Edición |
| `/administracion/usuarios/<pk>/estado/` | Activar/desactivar |
| `/administracion/grupos-permisos/` | Grupos y permisos |
| `/administracion/auditoria/` | Auditoría |

## Estructura de archivos

```text
apps/administration/
  models.py, forms.py, views.py, urls.py, selectors.py
  permissions_registry.py, role_setup.py, access.py, mixins.py
  services/{users,groups,audit}.py
  migrations/0002_setup_roles.py
templates/administration/
tests/test_administration_sprint02.py
```

## Ejecución local

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py setup_roles   # idempotente, si hiciera falta
pytest tests/test_administration_sprint02.py
npm run build
```

## Definition of Done

- [x] Pruebas Sprint 02 en verde.
- [x] Autorización en servidor (403).
- [x] Auditoría en operaciones críticas.
- [x] HTMX + navegación tradicional.
- [x] Tailwind compilado con estilos del panel.
