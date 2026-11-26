# Planning — Integrity Verification Service (IVS)

**Author of the TFG:** Alessa Renata Comparini Ceroni (`Alcompar77`)  
**Proposal:** Detection, response and integrity verification of clinical data after cyberattacks in hospital environments.

This repository is the **callee**. Daniel’s SaaS is only an HTTP client. Full boundary: [`BOUNDARY.md`](BOUNDARY.md).

## Goal

After a simulated incident (e.g. ransomware-like encryption, bit flips, insider edit), decide for each clinical object whether it is **intact**, **altered**, **encrypted_or_unreadable**, or **unknown**, against a cryptographic **trust baseline**. Produce reports, metrics, and a short regulatory analysis. Primary cases: electronic health record–like data and medical imaging (synthetic). Optional: unauthorised internal modification.

## Milestones

| ID | Outcome | Tests today |
|----|---------|-------------|
| **M0** | Own repo, contract copied, `/v1/health` real (`service=ivs`) | Passing |
| **M1** | Hash-only baselines + verify on `kind=file` (sha256) + basic report | Passing skeleton |
| **M2** | Signatures (e.g. Ed25519) + stronger report | `TODO(m2)` xfails |
| **M3** | Synthetic EHR + imaging corpus + attack harness | `TODO(m3)` xfails |
| **M4** | Metrics table + SIEM-shaped export + regulatory section | `TODO(m4)` xfails |
| **M5** | Joint demo with Daniel (URL swap, no merge) | `TODO(m5)` xfails |

## What this first PR ships

1. English README + planning + boundary docs.
2. Contract + OpenAPI v0.1.0 (same paths Daniel already soft-calls).
3. Runnable FastAPI IVS: health, baselines, verifications, reports (in-memory store, sha256 compare).
4. Large pytest battery: green for M0/M1; `xfail` + `TODO(mN)` markers for later work — clear them as you implement.

## How to work with Daniel

1. Keep `contract_version` / `x-contract-version` at `0.1.0` until both agree a bump.
2. Prefer additive fields under `object.clinical` over breaking JSON.
3. Never push IVS logic into his routers; never pull his OTP/credits into this repo.
4. Joint demo day: he sets `INTEGRITY_API_BASE_URL` to your deployment.

## Out of scope (Daniel’s TFG)

Tenant credits, OTP mail, WooCommerce, his Grafana, Linux VM provisioning, path guards on his storage.
