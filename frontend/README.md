# CreatorTrust — Frontend

React + TypeScript + Vite dashboard for the CreatorTrust FastAPI backend.

## Quickstart

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` and proxies `/api` to the
backend at `http://localhost:8000`.

## Environment variables

Copy `.env.example` to `.env` and adjust:

| Variable | Example | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL for direct API calls. |
| `VITE_OIDC_AUTHORITY` | `http://localhost:8080/realms/servalia` | OIDC issuer URL. |
| `VITE_OIDC_CLIENT_ID` | `creatortrust-frontend` | OIDC client ID. |
| `VITE_OIDC_REDIRECT_URI` | `http://localhost:5173/login/callback` | OIDC callback URL. |
| `VITE_OIDC_SCOPE` | `openid profile email` | Requested scopes. |
| `VITE_OIDC_POST_LOGOUT_REDIRECT_URI` | `http://localhost:5173/login` | Post-logout redirect. |

## Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Start Vite dev server. |
| `npm run build` | Type-check and build static files to `dist/`. |
| `npm run preview` | Preview the production build locally. |
| `npm run lint` | Run ESLint. |
| `npm run format` | Run Prettier. |
| `npm run format:check` | Check Prettier formatting. |

## Build & deploy

```bash
npm run build
```

Serve the contents of `dist/` with any static-file host (Nginx, Netlify, S3, etc.).
For local Docker Compose usage, see the root `docker-compose.yml`.
