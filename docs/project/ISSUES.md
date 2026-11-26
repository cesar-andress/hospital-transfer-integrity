# Issue backlog (paste into GitHub; assign after inviting collaborators)

Labels to create: `track:saas`, `track:api`, `track:joint`, `boundary`, `mvp`, `ambitious`.

---

## Milestone: MVP — December 2026

### D1 — Path guards green
- **Assignees:** Daniel  
- **Labels:** `track:saas`, `mvp`  
- **Body:** Clear every `TODO(path-guards)` under `saas/`. Upload sanitisation 400; OTP re-check under tenant root; unit helpers in place. `rg 'TODO(path-guards)' saas/` empty; `make test` green for those cases.

### D2 — Wire SaaS to monorepo IVS
- **Assignees:** Daniel  
- **Labels:** `track:saas`, `track:joint`, `mvp`  
- **Body:** Point `INTEGRITY_API_BASE_URL` at `api/` (compose / `docker-compose.joint.yml`). Soft-call on upload still must not brick demo if IVS down. Document env in `saas/.env.example`.

### A1 — Durable IVS store (leave memory behind)
- **Assignees:** Alessa  
- **Labels:** `track:api`, `mvp`  
- **Body:** Replace in-memory store with durable persistence (SQLite OK for MVP; Postgres welcome). Baselines/verifications survive restart. Tests cover restart or explicit flush semantics.

### A2 — IVS container + health for joint compose
- **Assignees:** Alessa  
- **Labels:** `track:api`, `mvp`  
- **Body:** Keep `api/Dockerfile` working; document `make run` and compose service `api:8090`. Contract health returns `service=ivs`.

### J1 — Joint happy-path script (upload → baseline → mutate → verify)
- **Assignees:** Daniel + Alessa  
- **Labels:** `track:joint`, `mvp`, `ambitious`  
- **Body:** One reproducible script/doc under `docs/` that shows intact then altered after a controlled mutation. Both packages required. No shared DB.

### B0 — Contract freeze acknowledgment 0.1.0
- **Assignees:** Daniel + Alessa  
- **Labels:** `boundary`, `track:joint`, `mvp`  
- **Body:** Both students confirm they read `docs/architecture/BOUNDARY.md` and `docs/contract/`. Comment ACK on the issue. No code.

---

## Milestone: Depth — February 2027

### D3 — Credits debit on download + ledger
- **Assignees:** Daniel · `track:saas` · `ambitious`

### D4 — Password hashing + Woo webhook HMAC
- **Assignees:** Daniel · `track:saas` · `ambitious`

### D5 — OTP lockout / rate limit
- **Assignees:** Daniel · `track:saas`

### D6 — Host-based tenant routing (nginx + API)
- **Assignees:** Daniel · `track:saas` · `ambitious`

### A3 — M2 signatures (e.g. Ed25519) on baselines
- **Assignees:** Alessa · `track:api` · `ambitious`

### A4 — M3 synthetic EHR + imaging corpus + attack harness
- **Assignees:** Alessa · `track:api` · `ambitious`

### A5 — First metrics table on synthetic corpus
- **Assignees:** Alessa · `track:api` · `ambitious`

### J2 — Contract bump process drill (additive clinical field)
- **Assignees:** both · `boundary` · `track:joint`  
- **Body:** Propose one additive `object.clinical` field; bump patch if needed; both sides green.

---

## Milestone: Complete — May 2027

### D7 — Storage abstraction toward real Linux VM (or documented ceiling)
- **Assignees:** Daniel · `track:saas` · `ambitious`

### D8 — Full security pass + demo polish
- **Assignees:** Daniel · `track:saas`

### A6 — M4 SIEM-shaped export + regulatory note
- **Assignees:** Alessa · `track:api` · `ambitious`

### A7 — M5 insider-modification secondary case
- **Assignees:** Alessa · `track:api` · `ambitious`

### J3 — Polished joint tribunal demo (script + timings)
- **Assignees:** both · `track:joint` · `ambitious`  
- **Body:** 10–15 minute demo: provision → upload → baseline → incident drill → verify → report/SIEM snippet → SaaS OTP path still healthy.

### J4 — Thesis evaluation pack (repro steps + metrics snapshot)
- **Assignees:** both · `track:joint`  
- **Body:** Frozen commands + expected tables for memory/thesis annex.
