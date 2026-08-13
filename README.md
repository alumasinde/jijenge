# Jijenge Public Content CMS — Backend phase

This phase adds a database-backed Public Content CMS without introducing a second database layer.

## 1. Copy the module

Copy:

```text
backend/app/Modules/PublicContent/
```

to the same path in your backend.

## 2. Add the migration

Copy:

```text
backend/migrations/101_create_public_content.sql
```

The current repository's latest migration is the branding migration at 100, so this phase uses 101.

## 3. Register the router

The package includes `backend/app/api_v1_routes_updated.py` as a ready-to-merge version of your current `backend/app/api/v1/routes.py`.

The only additions are:

```python
from app.Modules.PublicContent.routes import router as public_content_router
```

and:

```python
router.include_router(public_content_router)
```

## 4. Run migrations

From the repository root:

```bash
docker compose run --rm migrate
```

## 5. Endpoints

Public:

```text
GET /api/v1/public/content?locale=en-KE
```

Admin (existing ADMIN role required):

```text
GET    /api/v1/admin/public-content
POST   /api/v1/admin/public-content
PUT    /api/v1/admin/public-content/{id}
DELETE /api/v1/admin/public-content/{id}
```

The module uses the repository's existing `db_connection()` and existing `require_role("ADMIN")` authorization pattern. No credentials or database settings are hardcoded.

## 6. Tests

Run:

```bash
pytest backend/tests/test_public_content.py
```

or from `backend/`:

```bash
pytest tests/test_public_content.py
```
