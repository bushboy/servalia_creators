# CreatorTrust by Servalia

A publishing Mind for authors: one manuscript excerpt becomes governed marketing assets, KDP / IngramSpark packages, a launch plan, and an audit trail. The author’s Mind is called only from the API.

Hackathon track: **Content Repurposing Across Platforms**. Python FastAPI + React. Fintech RiskOps is not part of this app.

```
Author profile → excerpt → generate assets → governance → approve / revise
  → KDP / IngramSpark ZIP → launch plan → audit
```

## Setup (recommended): Docker Compose

You need **Docker Desktop** (or Docker Engine + Compose v2).

### 1. Environment file

```powershell
copy .env.example .env
```

On macOS/Linux: `cp .env.example .env`

Edit `.env` and set at least:

| Variable | Required | Notes |
|---|---|---|
| `PII_ENCRYPTION_KEY` | **Yes** | API container exits without it. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Yes | Defaults in `.env.example` work (`thebe` / `thebe` / `thebe`) |
| `MINDS_API_KEY`, `MINDS_MIND_ID`, `MINDS_MIND_EMAIL` | For live Mind chat | Server-side only. Never `VITE_*`. Omit them to still run generate-assets via local composition |

Leave `DATABASE_URL` pointing at localhost if you also run the API on the host. Compose **overrides** it to the `postgres` service.

### 2. Start the stack

```powershell
docker compose up --build
```

Wait until `creatortrust-api` is healthy (`curl http://localhost:8100/health`).

| What | URL |
|---|---|
| App | http://localhost:3080 |
| API | http://localhost:8100 |
| API docs | http://localhost:8100/docs |
| Keycloak | http://localhost:8180 |
| Postgres (on the host) | `localhost:5433` |

Ports are offset (`3080` / `8100` / `8180` / `5433`) so this can sit beside another Thebe stack.

### 3. Sign in

| Method | URL | Credentials |
|---|---|---|
| OIDC (Compose UI) | http://localhost:3080 | Keycloak user `test` / `test` (realm `servalia`) |
| API key (scripts / Vite) | — | `test-api-key:test-secret` |
| Keycloak admin | http://localhost:8180 | `admin` / `admin` |

Seeded author: **Mara Ellison**, book *Manuscript to Launch*.

### 4. Reset the demo

Does not drop Postgres, Keycloak, or the tenant. Restores Mara, the book, editions, and excerpt; removes generated assets and campaigns.

```powershell
python scripts/reset_demo.py
```

Or Settings → System → **Restore demo seed** (signed in as admin).

---

## Setup (optional): API and UI on the host

Use this when you want reload on save. Postgres/Keycloak can still come from Compose (`docker compose up postgres keycloak`).

### API

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

macOS/Linux: `source .venv/bin/activate`

Set:

```powershell
$env:SEED_TEST_TENANT = "1"
$env:PII_ENCRYPTION_KEY = "<fernet key>"
$env:DATABASE_URL = "postgresql+asyncpg://thebe:thebe@localhost:5433/thebe"
```

If you skip Compose Postgres, omit `DATABASE_URL` to use SQLite (`thebe.db`).

```powershell
uvicorn thebe_core.api:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Leave `VITE_OIDC_*` unset to sign in with `test-api-key:test-secret`. Vite proxies `/api` to **8100** by default; when the API is on 8000:

```powershell
$env:VITE_API_PROXY_TARGET = "http://localhost:8000"
npm run dev
```

---

## Tests

```powershell
pytest tests -q
cd frontend
npm test
```

E2E needs a seeded API:

```powershell
$env:E2E_API = "1"
npm run test:e2e
```


## Docs

| Doc | Purpose |
|---|---|
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | What is built, architecture, API |


