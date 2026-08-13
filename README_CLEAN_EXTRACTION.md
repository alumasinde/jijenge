# Jijenge Clean Backend + Frontend Package

This archive is arranged for extraction into the existing Jijenge project root.

- `backend/` -> existing backend
- `frontend/` -> existing frontend
- no temporary `backend-phase/` files
- no duplicate `package-lock.json` (pnpm is retained)
- no reference `api_v1_routes_updated.py`

The frontend source previously under `client/` has been moved to `frontend/`.

Important: the backend PublicContent module and migration are included. Ensure the existing
`backend/app/api/v1/routes.py` includes the PublicContent router before running the API.
