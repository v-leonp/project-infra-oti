# Sprint 03 — Catálogos maestros

## Objetivo

Administración centralizada de datos maestros (ODS, OES, sedes, proveedores, estados, tipos de servicio, responsables y tipos documentales) con control de acceso solo para **Administrador** y superusuarios.

## Rutas

Base: `/catalogos/` — ver `apps/catalogs/urls.py`.

## Modelos

App `apps.catalogs`: modelos con campos comunes (`code`, `is_active`, auditoría de usuario/fecha) y reglas por catálogo. Proveedores ↔ tipos de servicio (M2M). Responsables → sede (FK).

## Auditoría

Eventos `catalog_created`, `catalog_updated`, `catalog_activated`, `catalog_deactivated`, `catalog_relations_updated` en `AuditLog` (JSON sin secretos).

## Ejecución local

```bash
source .venv/bin/activate
python manage.py migrate
pytest tests/test_catalogs_sprint03.py
npm run build
```

## Definition of Done

- [x] CRUD lógico (sin borrado físico) en todos los catálogos.
- [x] HTMX en listados + fallback sin JS.
- [x] 403 para rol Usuario.
- [x] Pruebas Sprint 03 en verde.
