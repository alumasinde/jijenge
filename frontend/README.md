# Jijenge Frontend

Vite + React + TypeScript frontend for Jijenge.

## API configuration

The frontend reads the backend URL from `VITE_API_BASE_URL`.

Example:

```env
VITE_API_BASE_URL=https://your-backend-url.github.dev/api/v1
```

Do not add a trailing slash.

A local `.env` is included for the current Codespaces backend URL. `.env` is ignored by Git so the backend URL can be changed per environment without committing it.

## Development

```bash
npm install
npm run dev -- --host 0.0.0.0
```

## Build

```bash
npm run build
```

## Dynamic public data

The public pages load live data from:

- `GET /api/v1/branding`
- `GET /api/v1/services/categories`
- `GET /api/v1/services`

No service names or categories are hardcoded into the UI.
