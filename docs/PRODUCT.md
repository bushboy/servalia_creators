# CreatorTrust by Servalia

CreatorTrust is a publishing and marketing Mind for authors. It turns one manuscript excerpt into governed listing copy, campaign assets, and KDP / IngramSpark packages, with a persistent Mind that remembers voice, rights, and approvals.

It is not a generic copywriter and it does not publish on the author’s behalf. The author remains the operator.

| Layer | In this product |
|---|---|
| Public name | CreatorTrust by Servalia |
| Hackathon track | Content Repurposing Across Platforms |
| App | Python FastAPI (`thebe_core`) + React SPA |
| Governance | Servalia / Thebe policy engine + `creator_publishing` pack |
| Agent | One Minds agent per author (seeded as Mara), called only from the API |

Fintech RiskOps is not in this application.

## Loop

```
Author profile → excerpt → generate five assets → governance review
  → approve or reject / revise → KDP and IngramSpark ZIP
  → launch campaign board → audit trail
```

Protected demo path: **Manuscript → Repurpose → Govern → Approve → Package → Launch → Learn**

## What the app does

**Author and Mind.** Structured profile (voice, reader, rights, prohibited topics, approval policy) plus a `minds` row. Chat is `POST /authors/{id}/mind/message` as a job; the SPA polls `/jobs/{id}`. Without `MINDS_API_KEY` the chat endpoint returns 503 (no fake replies). Asset generation can still run via local composition.

**Book and editions.** A book is not a single SKU. Paperback and ebook are separate editions (ISBN, price, trim, platform flags, publishing status).

**Manuscript.** Upload `.txt` or `.md` to `data/uploads/`, with sha256, extracted text, rights declaration, and version.

**Assets.** Five types: book description, newsletter, social post, podcast pitch, video script. Each stores content, source references, assumptions, CTA, and risk notes.

**Governance.** YAML pack `CREATOR-*-001` (rights, privacy, claims, voice, platform metadata). Engine states PASS / PARTIAL / FAIL map to **Allow / Review / Block**. This is a creator-configured review, not legal clearance. The seeded guarantee sentence in the excerpt is meant to land on Review or Block.

**Approvals.** Evaluate → approve or reject → revise. Revisions record “Applied author preference” and a parent version.

**Packages.** KDP and IngramSpark ZIP adapters. Contents: `metadata.json`, `checklist.md`, `validation-report.json`, `SUBMIT.md`, excerpt if present. Status is manual (including Ingram proof-in-review). No live platform APIs.

**Launch.** Campaign with pre-launch, launch week, and post-launch tasks tied to approved assets.

**Audit.** Events for generate, evaluate, decide, package, and feedback applied. `customer_id` is the author id.

**Jobs.** In-process worker for `generate_assets`, `mind_message`, and `build_package`.

**Auth.** Keycloak OIDC (Compose: realm `servalia`, client `creatortrust-frontend`, UI on port 3080, Keycloak on 8180) or API key when OIDC env is omitted (`test-api-key:test-secret` with seed).

**Tenancy.** Authors, books, and assets are scoped to a tenant. Demo seed uses `test-tenant`.

## Screens

Author: **Home**, **Library**. Operators: **Audit**. Admins: Settings / Tenants.

| Route | Screen |
|---|---|
| `/` | Home — author, Mind chat, next step |
| `/author` | Author profile |
| `/library` | Books |
| `/books/:bookId` | Book workspace and editions |
| `/books/:bookId/manuscript` | Excerpt upload |
| `/books/:bookId/assets` | Generated assets |
| `/books/:bookId/governance` | Review, correction, regenerate |
| `/books/:bookId/publishing` | ZIP download and status |
| `/books/:bookId/launch` | Campaign board |
| `/audit` | Timeline |

## Seeded demo

With `SEED_TEST_TENANT` set:

- Author **Mara Ellison** (`seed-author-mara`)
- Book *Manuscript to Launch* (paperback + ebook)
- Excerpt includes: “This method guarantees that every new author will double their book sales.”
- Restore: Settings → System → Restore demo seed, `POST /admin/demo-reset`, or `python scripts/reset_demo.py`

## Architecture

```
SPA (React + TypeScript)
        │  session or API key  (never Minds secrets)
        v
FastAPI (thebe_core)
  authors, books, editions, documents, assets,
  packages, campaigns, audit, jobs
  PolicyEngine + creator_publishing
  JobService + AuditService
        │                    │
        v                    v
 Minds Builder API      PostgreSQL
 (optional)             data/uploads, data/packages
```

Internal storage still uses table `customers` for authors. Product language in the UI and API is authors, books, and assets.

## Domain

- **Author** — `customers` + `context`: name, biography, genres, reader, voice, prohibited topics, preferred terms, rights, approval policy
- **Mind** — mind id, email, status, skills, memory version
- **Book** — titles, series, description, publication strategy
- **Edition** — format, ISBN, language, trim, page count, price, platform strategy, publishing and proof-review status
- **Source document** — file, hash, text, rights, version
- **Asset** — type, platform, content, refs, assumptions, governance and approval status, parent version
- **Campaign / task** — phase, channel, approval and execution status

ISBN, files, format, and price live on the **edition**.

## Governance rules

| rule_id | Category | Effect |
|---|---|---|
| CREATOR-RIGHTS-001 | Rights | Block if rights missing or `unknown` |
| CREATOR-PRIVACY-001 | Privacy | Block if undeclared PII / named third party |
| CREATOR-CLAIM-001 | Claims | Review on guarantees / unsupported outcomes |
| CREATOR-VOICE-001 | Voice | Review on prohibited topics or weak preferred-term alignment |
| CREATOR-PLATFORM-001 | Platform | Review/Block on KDP publisher field and Ingram ISBN/format gaps |

## API

Creator routes on the FastAPI app (Compose UI proxies `/api` to the API):

```
POST/GET/PATCH     /authors[/{authorId}]
GET                /authors/{authorId}/mind/status
POST               /authors/{authorId}/mind/message     # job_id; poll GET /jobs/{id}

POST/GET/PATCH     /books[/{bookId}]
POST/GET/PATCH     /books/{bookId}/editions
PATCH              /editions/{editionId}

POST/GET           /books/{bookId}/documents
POST/GET           /books/{bookId}/generate-assets
GET                /books/{bookId}/assets

POST               /assets/{assetId}/evaluate|approve|reject|revise

POST               /editions/{editionId}/packages/kdp|ingramspark
GET/POST           /editions/{editionId}/publishing-status

POST/GET           /books/{bookId}/campaigns
GET                /books/{bookId}/campaigns/latest
GET                /books/{bookId}/audit

POST               /admin/demo-reset
GET/POST           /jobs[...]
```

## Not in this product

Live KDP or IngramSpark publish, PDF/DOCX extraction, email or social send, cover-file pipeline, billing, multiple Minds per author, or any RiskOps / FinOps / compliance-score UI.

The app does not claim automatic publication, legal copyright clearance, guaranteed sales, or official platform API access.
