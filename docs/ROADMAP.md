# Roadmap: ambitious, shared calendar

Dates match the GitHub milestones on `cesar-andress/hospital-transfer-integrity`.

| Gate | Due (Europe/Madrid EoD) | Meaning |
|------|-------------------------|---------|
| **MVP** | **2026-12-31** | Joint demo-able vertical slice |
| **Depth** | **2027-02-28** | Security + clinical realism |
| **Complete** | **2027-05-31** | Thesis-ready systems + evaluation |

Issues are intentionally ambitious; cut scope only with tutor ACK.

## MVP (due 2026-12-31): must show

**Daniel (`saas/`)**

- Path guards green (all `TODO(path-guards)` gone) — first PR inside this milestone.
- `vms` table, `max_accounts` and user invites.
- Upload soft-calls IVS baseline; OTP download still works.

**Alessa (`api/`)**

- Durable store (not only memory), health, baselines, verify, basic reports.
- Compose-ready image; Daniel points `INTEGRITY_API_BASE_URL` at `api/`.
- Contract tests green at `0.1.0`.

**Together**

- Scripted happy path: upload → baseline → mutate → verify (`intact` / `altered`).

## Depth (due 2027-02-28)

**Daniel:** credits on download; password hashing + webhook HMAC; OTP lockout; Host-based tenant routing started.

**Alessa:** M2 signatures (e.g. Ed25519); M3 synthetic EHR + imaging + attack harness; first metrics table; SIEM-shaped event draft.

## Complete (due 2027-05-31)

**Daniel:** Host routing solid; storage abstraction toward real Linux VM (or honest documented limit); full security hardening; polished demo.

**Alessa:** M4 metrics + SIEM export + regulatory note; insider-modification secondary case; joint demo polished; evaluation corpus reproducible.

---

Labels: `track:saas`, `track:api`, `track:joint`, `boundary`.
