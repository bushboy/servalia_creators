# CreatorTrust by Servalia

A publishing and marketing Mind for authors. CreatorTrust turns one manuscript into a governed publishing and marketing system: platform-ready packages for Amazon KDP and IngramSpark, campaign assets across email, social, podcast, and video, and a persistent Mind that remembers the author’s voice, rights, and approvals.

**Hackathon track:** Content Repurposing Across Platforms.

**Pitch:** CreatorTrust is a persistent publishing Mind that turns one manuscript into governed publishing and marketing assets across KDP, IngramSpark, email, social, podcast, and reader channels, without taking control away from the author.

This repository is a Python FastAPI + React app on Servalia / Thebe Core. It is **not** an ASP.NET rewrite. Fintech RiskOps (sometimes called FinOps) is out of this entry; judges should see only CreatorTrust.

## What it does

```
Create author profile
  → upload manuscript excerpt
  → generate publishing and marketing assets
  → validate against author rules
  → approve or reject
  → regenerate using feedback
  → produce KDP / IngramSpark packages
  → display launch plan and audit trail
```

- **Persistent Mind** — one Minds agent per author, called only from the API.
- **Governed repurposing** — book description, newsletter, social post, podcast pitch, and video script, each with source references.
- **Author-configured review** — voice, rights, privacy, unsupported claims, and platform metadata. Results are Allow / Review / Block, not legal clearance.
- **Assisted publishing** — ZIP packages and status tracking. The author remains the operator. No live autopublish.
- **Audit trail** — who generated, evaluated, approved, or revised each asset.

## Stack

| Layer | This repo |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind, shadcn |
| Backend | Python 3.13, FastAPI, SQLModel |
| Database | PostgreSQL (SQLite in some tests) |
| Jobs | In-process `JobService` |
| Auth | Keycloak OIDC + API keys |
| Governance | Servalia / Thebe policy engine + `creator_publishing` pack |
| Agent | Minds Builder API (server-side) |
| Deploy | Docker Compose |

## Quickstart

### Backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -e ".[dev]"
export SEED_TEST_TENANT=1
export PII_ENCRYPTION_KEY=WJUOLW0cIk_DxCa7xGy6Gw63wOVU4qZhG9vIzLJNxiQ=
# Minds (required for the live Mind demo; names may match the Builder API docs)
# export MINDS_API_BASE_URL=...
# export MINDS_API_KEY=...
uvicorn thebe_core.api:app --reload
```

Seeded API key: `test-api-key:test-secret`

```bash
pytest tests -q
```

### Frontend

```bash
cd frontend
npm install
# Leave VITE_OIDC_* unset for API-key login (see .env.example)
npm run dev
```

Open `http://localhost:5173`, sign in with the seeded key, then follow **Home → Library → book → manuscript → assets → governance → publishing**.

```bash
npx tsc -b
npm run test
# Full E2E (API must be running with SEED_TEST_TENANT=1):
E2E_API=1 npm run test:e2e
```

### Docker Compose

Host ports are offset so this stack can run beside another Servalia/Thebe compose file:

| Service | Container | Host port |
|---|---|---|
| Frontend | `creatortrust-frontend` | [http://localhost:3080](http://localhost:3080) |
| API | `creatortrust-api` | [http://localhost:8100](http://localhost:8100) |
| Keycloak | `creatortrust-keycloak` | [http://localhost:8180](http://localhost:8180) |
| Postgres | `creatortrust-postgres` | `localhost:5433` |

```bash
cp .env.example .env
docker compose up --build
```

Frontend image injects OIDC/API settings at start via `runtime-config.js`
(`OIDC_AUTHORITY`, `OIDC_CLIENT_ID`, `OIDC_REDIRECT_URI`, `API_BASE_URL`).
Keep Minds credentials on the API service only.

## Docs

| Doc | Purpose |
|---|---|
| `docs/PRODUCT.md` | What is built now, what is next, architecture, API, and claims |
| `docs/CREATORTRUST_CHECKLIST.md` | Remaining hackathon tasks only (live Mind, deploy, video, pack) |
| `docs/DEMO-VIDEO.md` | Three-minute recording script (story and narration) |
| `docs/DEMO-RUNBOOK.md` | Operator setup, seed reset, troubleshooting |
| `docs/EVIDENCE-CHECKLIST.md` | Screenshots and files for the submission pack |
| `docs/PITCH.md` | One-page pitch, pricing, roadmap |

Local Keycloak (Compose): realm `servalia`, client `creatortrust-frontend`, host port 8180. Omit `VITE_OIDC_*` to use API-key login. Public OIDC hygiene is on the remaining-work checklist.

## Out of scope (this sprint)

Live KDP or IngramSpark publishing, PDF/DOCX extraction, email/social posting, billing, multiple Minds, and any remaining fintech / RiskOps product surface.
