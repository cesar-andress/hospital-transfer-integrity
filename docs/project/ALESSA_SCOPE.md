# Alessa — full TFG scope (nothing left implicit)

Package: `api/`.  
Author of the TFG: Alessa Renata Comparini Ceroni (`Alcompar77`).  
Proposal: detection, response and integrity verification of clinical data after cyberattacks in hospital environments.

Canonical docs: `api/docs/PLANNING.md`, `api/docs/NEXT.md`, monorepo boundary [`../architecture/BOUNDARY.md`](../architecture/BOUNDARY.md), contract [`../contract/`](../contract/).  
Living spec: pytest under `api/tests/` (`xfail` + `TODO(mN)` = still to build).

This file is the **checklist against which the TFG is judged**. If it is not here and not marked Deferred, it is not required.

## Already Done (scaffold — do not throw away)

| Item | Evidence |
|------|----------|
| M0 health | `GET /v1/health` → `service=ivs`, contract `0.1.0` |
| M1 hash baselines / verify / basic report | In-memory store; unit + contract + `test_m1_*` green |
| Contract + OpenAPI in tree | Prefer monorepo `docs/contract/` as source of truth |
| Dockerfile | `api/Dockerfile` |
| Pytest battery with M2–M5 xfails | Clear markers as you implement |

## Must ship — mapped to GitHub issues

| Issue | Milestone | Covers | Acceptance gate |
|-------|-----------|--------|-----------------|
| **A1** Durable store | MVP | Persist baselines + verifications | Survive process restart; tests prove it |
| **A2** Container + health for joint compose | MVP | Runnable image on `:8090` | `make run` / compose; health `service=ivs` |
| **A3** M2 signatures | Depth | e.g. Ed25519 on baseline | Clear every `TODO(m2)` / xfail in `test_m2_signatures.py` |
| **A4** M3 EHR + imaging + attack harness | Depth | Synthetic corpora + flip/encrypt/insider | Clear every `TODO(m3)` in `test_m3_ehr_dicom_attacks.py` |
| **A5** First metrics on corpus | Depth | Detection rates / timing table | Partial metrics usable before full M4; align with A6 |
| **A6** M4 SIEM export + regulatory note | Complete | SIEM-shaped event + `docs/regulatory.md` | Clear every `TODO(m4)` in `test_m4_metrics_siem.py` |
| **A7** Insider modification secondary case | Complete | Unauthorised staff edit scenario | Documented case + tests; may overlap M3 insider xfail |
| **B0 / J1 / J2 / J3 / J4** | with Daniel | Boundary, joint demo, evaluation pack | Shared issues |

## Explicitly out of scope (Daniel’s TFG — do not implement)

| Topic |
|-------|
| Tenant billing / credits / WooCommerce |
| OTP mail / download UX |
| Path guards on SaaS storage |
| nginx Host routing / Linux VM provisioning |
| Grafana dashboards for the SaaS |
| Shared database with `saas/` |

## How “done” is proven

1. Issue checklist completed.  
2. Matching `TODO(mN)` / `@pytest.mark.xfail` **removed** and tests **pass** (`xfail_strict` is on).  
3. PR against `cesar-andress/hospital-transfer-integrity` `main`, English commits.  
4. No feature work under `saas/` except joint docs agreed in J-issues.

## Day-one commands

```bash
cd api
make install   # creates .venv + deps
make test      # expect many xfail for M2–M5; M0/M1 must pass
make run       # http://localhost:8090/v1/health
```
