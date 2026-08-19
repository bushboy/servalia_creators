# CreatorTrust by Servalia — Product

Version: 1.0.0-mvp  
Status: **The publishing loop is built and running in this repository.** Remaining work is live Minds credentials, a deployed demo, and the submission pack. Track those tasks in `docs/CREATORTRUST_CHECKLIST.md`.

## 1. Purpose

CreatorTrust is a publishing and marketing Mind for authors. It helps an author move from manuscript to published book and then manage an ongoing launch campaign while protecting the author’s voice, rights, approvals, and reader relationship.

It is not merely an AI copywriter. The core promise is:

> Turn one manuscript into a governed publishing and marketing system, with a persistent Mind that remembers the author and learns from every approval.

| Layer | Name |
|---|---|
| Public product | CreatorTrust by Servalia |
| Hackathon track | Content Repurposing Across Platforms |
| Company / platform (spoken, not in the nav) | Servalia |
| Governance engine | Servalia / Thebe Core (`thebe_core`) |
| Agent | the author’s Mind (seeded as “Mara”) |

Servalia is the trust layer: policy, approval, provenance, and audit. Minds is the persistent agent layer. CreatorTrust is the author-publishing vertical on top of both.

This product is **Python (FastAPI) and React**. It does not use ASP.NET. Fintech RiskOps is out of this entry; the running app is CreatorTrust only.

## 2. Positioning

Lead with repurposing plus control, not “compliance for authors.”

Authors need to scale their presence across platforms without losing their voice, rights, or control. CreatorTrust gives each author a persistent Mind that repurposes their work, checks every asset, and learns from their approvals.

The author remains the final operator. CreatorTrust prepares and validates platform-specific packages rather than silently publishing on the author’s behalf.

## 3. The problem

Independent authors and small publishing teams must turn one manuscript into many artefacts: listing copy, keywords, print and ebook metadata, newsletters, social posts, pitches, and a launch calendar. Generic AI writers produce volume without memory or control. They do not remember which claims the author rejected, which rights were declared, or which edition is actually going to KDP.

The result is fragmented marketing, inconsistent voice, and risky public claims — or a slow manual process the author cannot scale.

## 4. The solution

CreatorTrust binds one Mind to one author and runs a single loop:

```
Author profile
      ↓
Manuscript or excerpt
      ↓
Publishing package
      ↓
KDP and IngramSpark preparation
      ↓
Governance review
      ↓
Author approval
      ↓
Launch campaign
      ↓
Post-launch content and reader engagement
      ↓
Mind remembers feedback
```

Protected demo loop: **Manuscript → Repurpose → Govern → Approve → Package → Launch → Learn**

For **Amazon KDP**, it prepares metadata, manuscript and cover checklists, descriptions, keywords, and format-specific packages. The publisher field must contain only the author or publisher name.

For **IngramSpark**, it prepares print and ebook metadata, ISBN records, pricing, distribution choices, interior and cover file checklists, and proof-review tasks.

For **marketing**, it creates newsletters, social posts, podcast pitches, video scripts, reader magnets, launch announcements, and post-launch campaigns.

## 5. Core differentiator — governed author memory

The winning feature is not generation. It is memory plus gates:

- Remembers writing voice, target readers, and genres.
- Remembers prohibited claims and subjects.
- Remembers copyright and attribution preferences.
- Remembers which drafts the author approved or rejected.
- Flags privacy, rights, unsupported-claim, and brand-safety issues.
- Requires author approval before sensitive publishing actions.
- Records source material, versions, decisions, and platform status.

Sensitive actions that require explicit approval: publishing metadata, final cover or manuscript selection, rights declarations, distribution activation, public launch announcements, claims involving money, health, or professional outcomes, and use of personal stories or named third parties.

## 6. What is built now

The CreatorTrust vertical is implemented. A clean or seeded account can run the full loop in the SPA.

### Platform (Servalia / Thebe Core)

| Component | Role |
|---|---|
| Shared core (`thebe_core`) | FastAPI app, Pydantic models, provenance |
| Policy engine | YAML/JSON DSL, named predicates, Python callables; five-state results mapped to Allow / Review / Block |
| Audit store | SQLModel events with input/output snapshots; `customer_id` is the author id |
| Auth and tenancy | Keycloak OIDC + API keys, RBAC, `X-Tenant-Id` |
| Customer records | Reused as **authors**; voice, readers, rights, and approval policy live in `context` |
| Job worker | `generate_assets` and `build_package` |
| Document generator | Jinja2 for KDP/Ingram checklists and `SUBMIT.md` |
| Vertical pack | `verticals/creator_publishing/` |
| React SPA | Auth, layout, TanStack Query, CreatorTrust information architecture |
| Docker Compose | Postgres, Keycloak, API, frontend |

Internal names that stay: Python package `thebe_core`, SQL table `customers`. Product names in the API and UI are authors, books, and assets.

### Product loop

| Capability | In the running app |
|---|---|
| Author and Mind profile | Structured author data + `minds` row; conversation history is not the source of truth |
| Book and edition | Separate tables; paperback and ebook are not one product |
| Source documents | `.txt` / `.md` upload to `data/uploads/`, sha256, extracted text, rights declaration, version |
| Content generation | Five assets: description, newsletter, social post, podcast pitch, video script, each with type, platform, content, source refs, assumptions, CTA, risk notes |
| Minds chat | `POST /api/authors/{id}/mind/message` enqueues a job; the SPA polls `/jobs/{id}`. **503 until `MINDS_API_KEY` is set** — no fake chat |
| Asset generation fallback | Local composition when Minds is not configured, so the rest of the loop can be tested |
| Governance pack | Voice, rights, privacy, claims, platform metadata (`CREATOR-*-001`) |
| Approvals | Author self-approval; evaluate → approve or reject → revise with “Applied author preference” |
| Publishing packages | KDP and IngramSpark ZIP adapters; manual status; Ingram proof-review as status |
| Campaign board | Pre-launch, launch week, post-launch; tasks reference approved assets |
| Audit | Generate, evaluate, decide, package, feedback applied |
| Demo seed | Mara Ellison, book *Manuscript to Launch*, paperback + ebook, risky excerpt; restore from Settings → System without dropping tenants |

### Screens

Author nav: **Home**, **Library**. **Audit** for operators. Settings / Tenants for admins (omit from the recorded demo).

| Route | Screen |
|---|---|
| `/` | Home — author, Mind chat, next step |
| `/author` | Author profile (voice, reader, rights, prohibited topics, approval policy) |
| `/library` | Books list + create |
| `/books/:bookId` | Book workspace: titles, two editions |
| `/books/:bookId/setup` | Author setup on the book |
| `/books/:bookId/manuscript` | Upload excerpt, hash, rights declaration |
| `/books/:bookId/assets` | Five assets, source refs, assumptions |
| `/books/:bookId/governance` | Allow / Review / Block, correction, regenerate |
| `/books/:bookId/publishing` | ZIP download, checklist, manual status, proof-review |
| `/books/:bookId/launch` | Pre-launch / launch week / post-launch |
| `/audit` | Timeline with creator event types |

### Seeded demo

With `SEED_TEST_TENANT=1`:

- Author: **Mara Ellison** (`seed-author-mara`)
- Book: **Manuscript to Launch**
- Editions: paperback and ebook
- Excerpt includes: “This method guarantees that every new author will double their book sales.”
- Sign-in: `test-api-key:test-secret` when OIDC env is omitted
- Restore: Settings → System → Restore demo seed (admin), or `POST /api/admin/demo-reset`

## 7. Architecture

```
CreatorTrust SPA (React + TypeScript)
        │  session / API key  (never Minds credentials)
        v
Servalia / Thebe Core (FastAPI)
  /authors  /books  /editions  /documents  /assets
  /packages  /campaigns  /audit
  PolicyEngine + creator_publishing predicates
  JobService (generate_assets, build_package)
  AuditService
        │                    │
        v                    v
 Minds Builder API     PostgreSQL + data/uploads + data/packages
 (MINDS_API_* env)
```

The browser calls Servalia only. Servalia calls Minds when `MINDS_API_BASE_URL` and `MINDS_API_KEY` are set.

External destinations: Minds Builder API, KDP export ZIP, IngramSpark export ZIP. Email/social send is later.

### Auth (local)

- API-key login when `VITE_OIDC_*` is omitted.
- Docker Compose Keycloak: realm `servalia`, client `creatortrust-frontend`, host port **8180**; SPA on **3080**.
- Public OIDC (HTTPS, exact redirect URIs, no wildcards) is remaining work if the live demo uses Keycloak. See `docs/CREATORTRUST_CHECKLIST.md`. A FastAPI BFF with httpOnly cookies is out of scope for this sprint.

## 8. Domain model

**AuthorProfile** (stored as `customers` + `context`): display name, biography, genres, target reader, voice profile, prohibited topics, preferred terms, rights policy, approval policy.

**MindProfile:** author id, mind id, mind email, status, active skills, last interaction, memory version.

**Book:** working title, final title, subtitle, series, description, status, publication strategy.

**BookEdition:** format, ISBN, language, trim size, page count, interior/cover URIs, list price, currency, publication date, platform strategy, publishing status, proof-review status.

**SourceDocument:** file URI, name, mime type, sha256, extracted text, rights declaration, version.

**Asset:** type, platform, content, source references, assumptions, CTA, risk notes, governance status, approval status, parent version.

**Campaign / CampaignTask:** type, launch date, phase, channel, scheduled time, approval and execution status.

ISBN, files, format, price, and trim size belong on the **edition**, never only on the book.

## 9. Governance model

Same engine, creator rule pack. Decisions:

| Product | Engine |
|---|---|
| ALLOW | PASS |
| REVIEW | PARTIAL |
| BLOCK | FAIL |

| rule_id | category | decision |
|---|---|---|
| CREATOR-RIGHTS-001 | rights | BLOCK if rights missing or `unknown` |
| CREATOR-PRIVACY-001 | privacy | BLOCK if undeclared PII / named third party |
| CREATOR-CLAIM-001 | claims | REVIEW if guarantee / “will double” / unsupported outcome |
| CREATOR-VOICE-001 | voice | REVIEW if prohibited topic or missing preferred-term alignment |
| CREATOR-PLATFORM-001 | platform metadata | REVIEW/BLOCK on KDP publisher-field and Ingram ISBN/format gaps |

Do not call a result a legal clearance or copyright determination. Call it a **creator-configured governance review**.

Demo risk case: “This method guarantees that every new author will double their book sales.” must surface as an unsupported guarantee and require revision.

## 10. API (as built)

Mounted on the existing FastAPI app under `/api`. Authors self-approve; document SoD is not used.

```
POST/GET/PATCH     /api/authors[/{authorId}]
GET                /api/authors/{authorId}/mind/status
POST               /api/authors/{authorId}/mind/message   # returns job_id; poll GET /jobs/{id}

POST/GET/PATCH     /api/books[/{bookId}]
POST/GET/PATCH     /api/books/{bookId}/editions  /api/editions/{editionId}

POST/GET           /api/books/{bookId}/documents
POST/GET           /api/books/{bookId}/generate-assets  /api/books/{bookId}/assets

POST               /api/assets/{assetId}/evaluate|approve|reject|revise

POST               /api/editions/{editionId}/packages/kdp|ingramspark
GET/POST           /api/editions/{editionId}/publishing-status

POST/GET           /api/books/{bookId}/campaigns  /api/campaigns/{campaignId}
GET                /api/books/{bookId}/campaigns/latest
GET                /api/books/{bookId}/audit

POST               /api/admin/demo-reset
```

ZIP contents: `metadata.json`, `checklist.md`, `validation-report.json`, `SUBMIT.md`, excerpt if present. Demo filenames: `creatortrust-kdp-paperback.zip`, `creatortrust-ingramspark-paperback.zip`.

## 11. Target users

- Independent authors preparing a first or next book for KDP and IngramSpark.
- Small publishing teams that need coordinated listing copy and launch assets without giving an agent publish rights.
- Later (not this sprint): agencies and publishers running many author Minds on the same Servalia core.

## 12. What still needs to be built for the hackathon

The product loop is complete. Competing in the hackathon now depends on **proving** it live, not adding product surface.

| Need | Why it matters | Where |
|---|---|---|
| **Live Minds credentials** | Chat is the differentiator. Without `MINDS_API_BASE_URL` and `MINDS_API_KEY`, Home chat returns 503. Asset generation can still run via local composition. | `.env` / Compose API service |
| **Stable deployed demo** | Judges need a URL, not only localhost. | Hosting + Compose or equivalent |
| **Live demo URL** | Submission field. | Checklist |
| **Three-minute video** | Primary judging artefact. Script: `docs/DEMO-VIDEO.md`. Operator setup: `docs/DEMO-RUNBOOK.md`. No RiskOps chrome. | Checklist |
| **Pitch deck** | One-pager exists (`docs/PITCH.md`); slides do not. | Checklist |
| **Audit-trail screenshots** | Evidence pack for the application. | Checklist |
| **Investment application** | Evening pack. | Checklist |
| **Public OIDC hygiene** | Only if the live URL uses Keycloak (HTTPS, exact redirects, no wildcards). API-key login is enough for a recorded demo. | Checklist |

Empty, loading, and error states, clean-account loop, demo reset, ZIP contents, and “no Minds secrets in the frontend” are already in the app.

## 13. Out of scope (do not build this sprint)

- Live KDP / IngramSpark APIs or autopublish
- PDF/DOCX extraction, S3, cover-file pipeline, deep ISBN validation
- Email / social sending
- Multiple Minds per author
- Campaign date-change cascades
- Voice NLP / stylometry
- BFF httpOnly sessions
- Billing / metering
- Dual-vertical switcher
- Restoring `fintech_compliance` in this repo
- ASP.NET rewrite

## 14. Business model (illustrative)

- Self-serve: subscription per author or per active book, with Mind usage included.
- Studio: small presses running several author Minds under one tenant.
- Later: agencies on the same Servalia governance core.

Investment story: CreatorTrust is the Minds-native wedge; Servalia remains the platform. Recurring usage is one Mind per author, used on every campaign and every correction.

## 15. Roadmap

1. **Hackathon MVP (done in this repo):** one loop — profile, excerpt, five assets, governance, approval, two ZIPs, launch board, audit. No visible fintech product.
2. **Submit (now):** live Mind, deploy, video, deck, application. See `docs/CREATORTRUST_CHECKLIST.md`.
3. **After the demo:** cover files, richer ISBN rules, PDF/DOCX text extraction, object storage.
4. **Distribution:** optional partner APIs or browser-assisted submit; still author-operated.
5. **Platform reconstitution:** restore a fintech vertical in a common Servalia repo without putting it in this entry.
6. **Expansion:** agencies, multi-book catalogues, reader-community workflows.

## 16. What not to claim

Do not claim automatic publication on KDP or IngramSpark, legal copyright clearance, complete infringement detection, guaranteed sales or ranking, fully autonomous publishing, or official platform API access unless verified.

Use:

> CreatorTrust prepares, validates, and governs author-controlled publishing workflows for KDP and IngramSpark.

The running app must not mention RiskOps, FinOps, Companies, POPIA, FICA, AML, KYC, DPIA, or a compliance score.

## 17. Definition of done (hackathon)

A deployed MVP where a clean or seeded account can: create an author profile, upload an excerpt, generate five assets, see a Review or Block on the seeded guarantee, approve or reject and regenerate, download KDP and IngramSpark packages, and view a launch plan plus audit trail.

Still open: real Mind replies in the recorded demo, a live URL, and a video with no RiskOps chrome.
