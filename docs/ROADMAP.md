# Roadmap — ambitious, shared calendar

| Gate | Date | Meaning |
|------|------|---------|
| **MVP** | **2026-12-19** (Friday, Europe/Madrid) | Joint demo-able vertical slice |
| Mid checkpoint | **2027-02-27** | Depth: security + clinical realism |
| **Complete** | **2027-05-15** | Thesis-ready systems + evaluation |

Milestones on GitHub mirror these gates. Issues are intentionally ambitious; cut scope only with tutor ACK.

## MVP (December 2026) — must show

**Daniel (`saas/`)**

- Path guards green (all `TODO(path-guards)` gone).
- Upload → soft-call IVS baseline → OTP download still works.
- Tenant isolation acceptance suite mostly green (no Host/credits stretch yet if marked later).

**Alessa (`api/`)**

- M0/M1 productionized: durable store (not only memory), health, baselines, verify, basic reports.
- Compose-ready image; Daniel points `INTEGRITY_API_BASE_URL` at `api/`.
- Contract tests green at `0.1.0`.

**Together**

- One scripted happy path: upload clinical stand-in → baseline id stored → mutate file in a drill → verify → `altered` or `intact` shown in SaaS audit / IVS report.

## February 2027 — depth

**Daniel:** credits on download; password hashing + webhook HMAC; OTP lockout; Host-based tenant routing started.

**Alessa:** M2 signatures (e.g. Ed25519); M3 synthetic EHR + imaging cases + attack harness; first metrics table; SIEM-shaped event draft.

## May 2027 — complete

**Daniel:** Host routing solid; storage abstraction toward real Linux VM (or honest documented limit); full security hardening; polished demo.

**Alessa:** M4 metrics + SIEM export + regulatory note; M5 joint demo polished; insider-modification secondary case; thesis evaluation corpus reproducible.

---

See issue labels `track:saas`, `track:api`, `track:joint`, `boundary`.
