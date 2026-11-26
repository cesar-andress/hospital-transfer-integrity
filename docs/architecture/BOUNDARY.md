# System boundary — authoritative (read once, change rarely)

**Owner of this document:** tutor (`cesar-andress`).  
**Students:** Daniel (`dani84mol`) owns `saas/`. Alessa Renata Comparini Ceroni (`Alcompar77`) owns `api/`.  
**Rule:** if a change would move work across this wall, open an issue first. Do not “help” by implementing the other side.

---

## 1. One story, two products

Hospital demo story:

1. A hospital **tenant** uploads a clinical artefact through the **transfer SaaS** (`saas/`).
2. The SaaS **soft-calls** the **Integrity Verification Service** (`api/`) to register a trust baseline (and later to verify after a simulated incident).
3. The IVS returns a structured **verdict**. The SaaS stores ids for audit and continues OTP / credits / download.
4. The IVS can also run **standalone** demos (synthetic EHR/imaging, attack harness, SIEM-shaped export) without the SaaS UI.

They share **HTTP + a versioned JSON contract**. They do **not** share a database, ORM, auth users table, or deployment identity beyond a demo token.

```
                    ┌─────────────────────────────────────────┐
                    │   hospital-transfer-integrity (monorepo)│
                    │                                         │
   Tenant user      │   saas/ (Daniel)      api/ (Alessa)     │
        │           │   Transfer SaaS  ──►  IVS callee        │
        │  upload   │   OTP, tenants,       baselines,        │
        └──────────►│   credits, FS/VM      verify, reports   │
                    │   Woo, front          EHR/DICOM cases   │
                    │         ▲                    │          │
                    │         └── docs/contract ───┘          │
                    └─────────────────────────────────────────┘
```

---

## 2. Ownership matrix (non-negotiable)

| Concern | `saas/` Daniel | `api/` Alessa |
|---------|----------------|---------------|
| Multi-tenant accounts, JWT, Host routing | **Yes** | No |
| Filesystem / “VM” isolation, path guards | **Yes** | No |
| OTP download links, credits, WooCommerce | **Yes** | No |
| Front-end transfer UX | **Yes** | No |
| `POST /v1/baselines`, `/v1/verifications`, `/v1/reports` | Client only | **Yes** |
| Cryptographic baselines / signatures | No | **Yes** |
| Synthetic EHR + medical imaging corpora | No | **Yes** |
| Attack simulation (encrypt / alter / insider) | No | **Yes** |
| Metrics, SIEM-shaped events, regulatory note | No | **Yes** |
| Contract OpenAPI (`docs/contract/`) | Propose + review | Propose + review |
| Shared PostgreSQL / Redis between packages | **Forbidden** | **Forbidden** |

---

## 3. Integration contract (the only weld)

Canonical files:

- [`docs/contract/CONTRACT.md`](../contract/CONTRACT.md)
- [`docs/contract/openapi-integrity.yaml`](../contract/openapi-integrity.yaml)

| Field | Value |
|-------|--------|
| Current `contract_version` / `x-contract-version` | `0.1.0` |
| Transport | HTTP JSON |
| Auth (demo) | Header `X-Integrity-Token` (optional until Alessa flips `IVS_REQUIRE_TOKEN`) |
| SaaS config | `INTEGRITY_API_BASE_URL`, `INTEGRITY_SHARED_TOKEN` |
| Failure policy (SaaS) | Soft-fail: log + continue upload if IVS down (demo must not brick) |

**Versioning discipline**

- Additive optional JSON fields → patch; both students ACK in the same issue.
- Breaking rename/removal → minor/major bump **before** merge; both packages green on CI.
- Prefer `object.clinical` (open object) for Alessa-only metadata so Daniel’s client stays thin.

**Ids that may cross the wall:** `tenant_id`, `transfer_id`, `baseline_id`, `verification_id`. Nothing else.

---

## 4. Runtime topology

| Process | Default port | Package |
|---------|--------------|---------|
| IVS (FastAPI) | `8090` | `api/` |
| SaaS API | per `saas/` compose | `saas/` |
| Echo stub inside `saas/services/integrity-stub` | transitional | **Deprecated** once `api/` is the compose target |

Target: root or saas compose sets `INTEGRITY_API_BASE_URL=http://api:8090` and runs the real IVS. Keep the stub only as a local fallback documented in `saas/docs/integration/DANIEL_HOOK.md`.

---

## 5. Collaboration protocol

1. **Work in a fork** of `cesar-andress/hospital-transfer-integrity`. Open PRs against `main`.
2. **One theme per PR.** Prefer paths under only `saas/` **or** only `api/` unless the PR is a coordinated contract bump (then both + `docs/contract/`).
3. **Tests gate merge.** `saas`: existing make targets. `api`: `make test`. Contract tests must stay green.
4. **Do not implement the other student’s TFG** “as a favour”. File an issue and assign them.
5. **Joint demo** is a milestone deliverable, not a reason to merge codebases.

---

## 6. Anti-patterns (reject in review)

- Importing Python modules from `saas/` into `api/` (or the reverse).
- Writing IVS rows into the SaaS Postgres schema.
- Putting OTP / credit logic in `api/`.
- Putting Ed25519 / DICOM parsers / ransomware harness in `saas/`.
- Silent contract drift (OpenAPI out of date with handlers).
- Monorepo “utils” that become a third shared product.

---

## 7. Freeze policy

This boundary is **stable**. Edits require tutor approval. Students propose changes via issue labelled `boundary`; they do not silently rewrite this file in feature PRs.
