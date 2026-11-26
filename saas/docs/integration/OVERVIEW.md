# Integration boundary — Daniel (MVP-Saas) × Alessa Renata Comparini Ceroni (clinical integrity)

Two TFGs, one demo story. They share a **HTTP contract**, not a codebase.

| Student | Owns | Does **not** own |
|---------|------|------------------|
| **Daniel** (`dani84mol/MVP-Saas`) | Multi-tenant transfer SaaS: tenants, “VM” storage, OTP links, credits, Woo provision, front | Crypto baselines, clinical ontology, SOC/SIEM adapters, integrity reports, DICOM/EHR analysis |
| **Alessa Renata Comparini Ceroni** (own repo — **cyber / clinical integrity TFG**) | Integrity Verification Service (IVS): register baseline, verify after incident, reports, synthetic EHR/imaging cases, attack sims, SOC/SIEM export, metrics, regulatory notes | Tenant billing, OTP UX, nginx routing, Linux VM orchestration, path guards, credits |

## Story that ties them

1. A hospital tenant uploads a clinical artefact through Daniel’s SaaS.
2. Daniel’s API asks Alessa’s IVS to **register** a trust baseline (or later to **verify** after a simulated ransomware).
3. IVS answers with a structured verdict. Daniel stores the verdict id next to the transfer (audit), and continues its own flow (OTP, credits, …).
4. Alessa can also run standalone: ingest synthetic records, simulate attack, verify, export SIEM-oriented events — without Daniel’s UI.

Until Alessa’s service exists, Daniel talks to a **local echo stub** that accepts the same JSON and returns it almost unchanged with `verdict=passthrough`. Swapping the URL is enough to point at Alessa’s real deployment.

## Repos and artefacts

| Artefact | Where | Who updates |
|----------|--------|-------------|
| OpenAPI + examples | `docs/integration/CONTRACT.md` + `openapi-integrity.yaml` | Both (versioned; bump `x-contract-version`) |
| Stub server (echo) | `services/integrity-stub/` | Daniel keeps it for demos; Alessa may copy as her skeleton then replace guts |
| HTTP client | `backend/app/integrity_client.py` | Daniel |
| Work plan Alessa | `docs/integration/ALESSA_WORKPLAN.md` | Tutor + Alessa Renata Comparini Ceroni |
| Hook guide Daniel | `docs/integration/DANIEL_HOOK.md` | Daniel |

## Non-goals (avoid collisions)

- Alessa does **not** implement OTP, tenant quotas, or WooCommerce.
- Daniel does **not** invent signature algorithms, DICOM parsers, or SIEM pipelines.
- No shared database. Only HTTP + ids (`tenant_id`, `transfer_id`, `baseline_id`, `verification_id`).
## Versioning

Contract field `x-contract-version` (semver). Breaking JSON changes → minor/major bump and a short note in both READMEs. Additive optional fields → patch.
