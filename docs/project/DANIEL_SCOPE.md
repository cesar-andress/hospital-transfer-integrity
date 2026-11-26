# Daniel — full TFG scope (nothing left implicit)

Package: `saas/`.  
Canonical product docs: `saas/README.md` (requirements matrix R01–R26), `saas/docs/SPEC.md`, `saas/docs/NEXT.md`.  
Living spec: acceptance tests under `saas/backend/tests/` (`xfail` = still to build).

This file is the **checklist against which the TFG is judged**. If it is not here and not marked Deferred, it is not required.

## Already Done (do not re-implement)

| Id | Topic |
|----|--------|
| R01 | Admin creates companies |
| R02 (demo) | Woo auto-provision (unsigned — harden in D6) |
| R03 (partial) | Second purchase tops up same tenant (quota today; ledger in D4) |
| R04 (FS) | One storage root per tenant (table `vms` in D3; real Linux in D7) |
| R08 | Shared front |
| R09 | JWT tenant isolation |
| R16 (base) | Prometheus / Grafana base |
| R21 (base) | `audit_logs` |
| R22 | Automated tests |
| R23 | Product docs (English) |
| Soft IVS client | `integrity_client` soft-call on upload (point URL in D2) |

## Must ship — mapped to GitHub issues

| Issue | Milestone | Covers | Acceptance gate |
|-------|-----------|--------|-----------------|
| **D1** Path guards | MVP (due 2026-12-02 inside MVP) | R07, R11 path part | No `TODO(path-guards)`; listed tests green |
| **D2** Wire SaaS → monorepo `api/` | MVP | Joint hook | Compose/`INTEGRITY_API_BASE_URL`; soft-fail preserved |
| **D3** `vms` + invites + `max_accounts` | MVP | R04 table, R05, R06 | `test_tenancy_model` invite/max xfails green |
| **D4** Credit ledger | Depth | R03 ledger, R12–R15 | `test_credits.py` xfails green |
| **D5** Host routing | Depth | R10 | `test_routing.py` Host xfails green |
| **D6** Security hardening | Depth | R02 HMAC, R11 attempts, R17–R20, OTP hash/single-use/Host bind | matching xfails in `test_tenancy_model`, `test_otp_download`, `test_routing` |
| **D7** Real Linux VM or documented limit | Complete | R24 | `app.storage` + VM xfails green **or** written limit in README |
| **D8** Demo polish + security pass | Complete | R16 stretch metrics optional | Demo script + checklist below |
| **B0 / J1 / J3 / J4** | with Alessa | Boundary + joint demo | Shared issues |

## Explicitly Deferred (out of TFG — Daniel cannot be asked for these)

| Id | Topic |
|----|--------|
| R25 | Byte quotas |
| R26 | Managed TLS / custom domains |
| HA / fancy billing / multi-region | Not in matrix |

## Alessa’s side (Daniel does **not** own)

Crypto baselines, signatures, EHR/DICOM corpora, attack harness, SIEM export, regulatory note, IVS reports guts.  
Daniel only: HTTP client + env URL + soft-fail (D2) and joint scripts (J1/J3).

## How “done” is proven

1. Issue checklist completed.  
2. Matching `@pytest.mark.xfail` / `TODO(...)` **removed** and tests **pass**.  
3. PR against `cesar-andress/hospital-transfer-integrity` `main`, English commits.  
4. No work under `api/` except contract ACK / joint docs agreed in J-issues.
