# CreatorTrust demo runbook

Operator only. The recording script is `docs/DEMO-VIDEO.md`. Do not put this file, these credentials, or these URLs on camera.

Do not show Companies, checklists, DPIAs, or a percentage score. Do not open Settings or Tenants in the recorded video except when resetting the seed **before** you press record.

---

## 1. What you need to run it

| Need | Where |
|---|---|
| Running stack | Docker Compose: frontend [http://localhost:3080](http://localhost:3080), API [http://localhost:8100](http://localhost:8100) |
| Minds credentials on the **API** | `.env`: `MINDS_API_BASE_URL`, `MINDS_API_KEY`, `MINDS_MIND_ID`, `MINDS_MIND_EMAIL`. Never `VITE_*`. Never in the browser. |
| Seeded tenant | `SEED_TEST_TENANT=true` on the API. Author **Mara Ellison**, book *Manuscript to Launch*, paperback + ebook, risky excerpt |
| Sign-in (Compose) | Keycloak user `test` / `test`, realm `servalia` |
| Guarantee sentence in the excerpt | Seeded from `verticals/creator_publishing/sample_excerpt.txt` |

You do **not** need a cover file, PDF, live KDP/Ingram login, or email/social send.

---

## 2. Configure the Mind

Credentials belong only on the API service.

```
MINDS_API_BASE_URL=https://api.build.hellominds.ai
MINDS_API_KEY=<your builder API key>
MINDS_MIND_ID=<the Mind UUID>
MINDS_MIND_EMAIL=<the Mind email>
MINDS_CONVERSATION_ALIAS=creatortrust
```

Use the host with no `/v1` suffix. A trailing `/v1` is stripped. Auth header is `X-Api-Key`.

After changing `.env`:

```powershell
docker compose up -d --force-recreate api
```

Wait for `http://localhost:8100/health`. Then restore the seed (below). If the Mind row was created before credentials existed, it still has a placeholder id until you reset.

### Without Compose

Host API on port 8000 + Vite at `http://localhost:5173` with `VITE_OIDC_*` unset: sign in with `test-api-key:test-secret` (`SEED_TEST_TENANT=1` on the API). Same seed restore. Keep Minds vars on the API process only.

---

## 3. Sign-in and reset

| Mode | URL | Credentials |
|---|---|---|
| Docker Compose | [http://localhost:3080](http://localhost:3080) | OIDC `test` / `test` |
| Vite + host API | [http://localhost:5173](http://localhost:5173) | API key `test-api-key:test-secret` |
| Keycloak admin (never on camera) | [http://localhost:8180](http://localhost:8180) | `admin` / `admin` |

**Restore exact expected state:** Settings → System → Restore demo seed (admin). Compose maps the `test` user to tenant admin via `SEED_OIDC_TEST_USER_SUB`.

After reset, Home should show **Mara Ellison**, book *Manuscript to Launch*, and a connected Mind — not “credentials not configured on the API”.

Reset before every recording. Capture the audit trail after a dress rehearsal if you need a backup screenshot; still perform the minimum live actions on camera.

---

## 4. Dress rehearsal (click path)

Follow `docs/DEMO-VIDEO.md` for what to say. This is the operator path.

1. **Home.** Confirm Mara, voice, reader, *Manuscript to Launch*. Send: *What voice and claims should we avoid for this launch?* Wait — replies often take one to two minutes. Do not refresh. **Do not continue if chat is a 503 or a fake reply.**
2. Optional flash: **Edit profile** — voice, rights `all_rights_owned`, prohibited topics include guaranteed income and guaranteed sales. Do not edit on camera unless you mean to.
3. Skip a Library tour. Open the book only if you need editions. ISBN and price live on the edition.
4. **Manuscript.** Seeded `sample_excerpt.txt`. Confirm rights, then scroll to the guarantee sentence. Hash lives under **Technical details**. Re-upload only if missing (`.txt` / `.md`).
5. **Assets → Generate assets.** Wait for five cards. If the Mind does not return JSON, local composition still fills the five types so the loop can continue. Point at source references and rights on one card. The **book description** is the asset that contains the guarantee.
6. **Governance → Run review** on the **book description**. Expect Review or Block on the guarantee. Correction: *Do not use guaranteed results or aggressive sales language.* **Reject**, then **Revise**. Confirm **Applied author preference** and version **v2**. **Approve** the corrected description — packages are gated on this.
7. **Publishing.** Paperback: download both ZIPs. Unzip: `metadata.json`, `checklist.md`, `validation-report.json`, `SUBMIT.md`. **Proof in review** is status only.
8. **Launch → Create launch plan.**
9. **Audit.** Filter `seed-author-mara`. Confirm generate, evaluate, reject, revise, package.

---

## 5. Fallback strategy (recording)

Live Mind chat is the only dynamic dependency.

| Situation | What to do |
|---|---|
| Mind replies, but slowly | Stay on **Waiting for the Mind…**. Do not refresh. |
| Mind chat 503 / not configured | **Stop.** Fix credentials. Do not record a fake conversation. |
| Mind chat works, generate is slow or prose-only | Local composition may fill assets. That is allowed for the loop. Chat remains the live-Mind proof. |
| Live Mind down at record time | Use a **clearly labelled** screenshot or clip of a *previous real* reply. Never present a fallback as live. |
| Seed dirty | Restore demo seed, then only the minimum live clicks. |

Preload author, manuscript, and (if needed) generated assets via seed + one generate pass before recording. Then on camera: one Mind question, governance reject/revise, package download, launch plan, audit.

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Credentials not configured | API missing `MINDS_*` | Fix `.env`, recreate `api`, restore seed |
| Chat 503 | `MINDS_API_KEY` missing inside the container | Confirm env **in** `creatortrust-api` |
| Chat 401 / 403 | Bad or expired Builder key | Replace `MINDS_API_KEY`. Header is `X-Api-Key`, not Bearer |
| Chat 502 | Builder error after send/wait | Logs on `creatortrust-api` for `/v1/messaging/...` |
| Chat 504 | Old blocking proxy | Recreate **api and frontend**; chat enqueues a job and polls |
| Wrong Mind | Stale `mind_id` or alias | Restore seed; optional new `MINDS_CONVERSATION_ALIAS` |
| Generate job warning, assets still appear | Mind returned prose; local composition used | Fine for the loop; chat is still the live proof |
| ZIP buttons disabled | Description not approved, or still Block | Approve a non-Block description |
| No Settings / restore | Not admin | Compose `test` user or API key `test-api-key:test-secret` |
| RiskOps / Companies copy | Stale frontend | Stop. Rebuild. Do not record |

---

## 7. What not to claim

Automatic publication, legal copyright clearance, guaranteed sales, official KDP/Ingram APIs, or a fake Mind in the recorded demo.
