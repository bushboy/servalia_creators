# CreatorTrust checklist — remaining work

The product loop is implemented. Detail lives in `docs/PRODUCT.md`. Tick items as they land. A section is not done until its **acceptance** box is checked.

Completed Pass 1 (strip FinOps), Pass 2 (rebrand), and Pass 3 Days 1–6 (author, book, assets, governance, packages, launch, audit) have been removed from this file. Do not rebuild them.

Protected loop: Manuscript → Repurpose → Govern → Approve → Package → Launch → Learn

| Gate | Status |
|---|---|
| Pass 1–3 — Product loop | done |
| Phase 4 — Live Mind | pending credentials |
| Phase 4 — Deploy | pending |
| Phase 4 — Submission pack | pending |

---

## Phase 4 — Submit the hackathon entry

**Goal:** a live Mind, a stable URL, and a three-minute recording that matches `docs/DEMO-VIDEO.md`.

### 4.1 Live Mind

Home chat must talk to a real Mind through Servalia. Do not fake replies.

- [ ] Set `MINDS_API_BASE_URL` and `MINDS_API_KEY` on the API (never `VITE_*`)
- [ ] Bind seed Mind id / email (`MINDS_MIND_ID` / `MINDS_MIND_EMAIL`)
- [ ] Seeded author Mara messages the Mind from Home and gets a live reply

**Acceptance**

- [ ] Recorded or live demo shows a real Mind reply. Chat is not a 503.

### 4.2 Deploy

- [ ] Stable version deployed
- [ ] Live demo URL
- [ ] Seed restore works on the deployed instance (Settings → System, admin)
- [ ] No Minds secrets in the frontend bundle (`rg MINDS frontend/` stays clean)

If the live URL uses Keycloak (skip this block if the demo uses API-key login):

- [ ] HTTPS/TLS for public endpoints (`ssl=required` on the realm)
- [ ] Exact `redirectUris` and `webOrigins` for `creatortrust-frontend` — no wildcards
- [ ] Keycloak production mode (`KC_HOSTNAME` set; not `start-dev`)
- [ ] PKCE on the SPA client; no client secret in the browser
- [ ] Direct access grants disabled on the public SPA client
- [ ] Secrets in a secret manager, not committed Compose `.env`
- [ ] Login, silent renew, logout, and tenant create verified on the live host

Defer unless a production IdP is mandatory: external Postgres for Keycloak, SMTP, password policy, brute-force lockout, OTP/WebAuthn for admins, event log aggregation, unused-realm cleanup. A FastAPI BFF with httpOnly cookies is out of scope.

**Acceptance**

- [ ] Judges can open a URL and complete the loop (API key or OIDC).

### 4.3 Demo video

Script: `docs/DEMO-VIDEO.md`. Setup: `docs/DEMO-RUNBOOK.md`. Evidence: `docs/EVIDENCE-CHECKLIST.md`. Do not show Companies, checklists, DPIAs, or a percentage score.

- [ ] 0:00–0:20 Problem and promise
- [ ] 0:20–0:40 Mara and her Mind
- [ ] 0:40–1:05 Manuscript and source link
- [ ] 1:05–1:35 Five generated assets
- [ ] 1:35–2:10 Policy check, reject, revise, applied preference
- [ ] 2:10–2:35 Platform packages (ZIP contents)
- [ ] 2:35–2:55 Launch plan
- [ ] 2:55–3:00 Audit and closing overlay
- [ ] Three-minute video exported

**Acceptance**

- [ ] Video contains no RiskOps chrome and shows the full loop.

### 4.4 Submission pack

- [ ] Pitch deck (one-pager is `docs/PITCH.md`)
- [ ] Audit-trail screenshots
- [ ] Investment application

Already in repo: product description (`docs/PRODUCT.md`), architecture (in Product), pitch copy, roadmap, pricing hypothesis, Mind id/email env, demo reset.

**Acceptance**

- [ ] Application can be submitted with URL, video, deck, and screenshots.

---

## Definition of done

- [x] Product loop in the running app: excerpt → five assets → governance → approve/reject/revise → two ZIPs → launch board → audit
- [x] Guarantee sentence is Review or Block
- [x] Clean-account loop and demo reset work
- [x] README and PRODUCT describe CreatorTrust, not RiskOps
- [ ] Seeded author messages a real Mind through Servalia
- [ ] Stable demo URL
- [ ] Demo video contains no RiskOps chrome
- [ ] Submission pack complete

---

## Do not build (leave unchecked on purpose)

Cuts, not backlog for this sprint. See `docs/PRODUCT.md` §13.

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
