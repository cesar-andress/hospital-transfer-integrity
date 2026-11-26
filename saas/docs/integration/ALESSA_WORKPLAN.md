# Alessa Renata Comparini Ceroni: work plan (clinical integrity TFG)

Proposal (PDF): Detección, respuesta y verificación de integridad de datos clínicos frente a ciberataques en entornos hospitalarios.

You own the Integrity Verification Service (IVS). Daniel's SaaS is only a caller of your HTTP API. Copy [`CONTRACT.md`](CONTRACT.md) + [`openapi-integrity.yaml`](openapi-integrity.yaml) into your repo and treat `x-contract-version` as the shared agreement.

The folder `services/integrity-stub/` in Daniel's repo is a disposable echo. Your TFG replaces that behaviour behind the same paths.

## Deliverables that fill a full TFG

### A. Core IVS (must)

1. Baseline store: persist cryptographic evidence per object (`baseline_id`, hash, signature, algorithm, tenant_id, timestamps).
2. `POST /v1/baselines`: create baseline from payload and/or content hash (and later full clinical objects).
3. `POST /v1/verifications`: compare the current object with its baseline and return `intact` | `altered` | `encrypted_or_unreadable` | `unknown`.
4. `GET /v1/reports/{id}`: human-readable + machine-readable report (what changed, confidence).
5. Synthetic datasets
   - EHR-like documents / structured records.
   - Medical imaging samples (DICOM or anonymised stand-ins).
6. Attack simulation harness, flip bits, replace files, encrypt blobs (ransomware-like), unauthorised "insider edit".
7. Metrics, detection rate, false positives/negatives, time-to-verdict on the synthetic corpus.
8. Regulatory note, short analysis (e.g. integrity expectations under GDPR / healthcare guidance); not legal advice, academic framing.

### B. Integration / ops (should)

9. SOC/SIEM-shaped export, JSON/CEF-like event when verdict is not intact (Daniel may ignore; your demo shows the event).
10. Auth, validate `X-Integrity-Token` (or mTLS later); document rotation.
11. OpenAPI kept in sync with implementation; contract tests against the YAML.
12. Docker image Daniel can point `INTEGRITY_API_BASE_URL` at.

### C. Stretch (nice)

13. Secondary case: insider modification by "clinical staff" role.
14. Batch verify API for post-incident sweeps.
15. Simple UI or notebook for the simulator demo (optional; not Daniel's front).

## Suggested milestones

| Milestone | Outcome |
|-----------|---------|
| M0 | Own repo + copy contract; health endpoint real |
| M1 | Hash-only baselines + verify on files (wire with Daniel stub URL swap) |
| M2 | Signatures (e.g. Ed25519) + report resource |
| M3 | EHR + imaging synthetic cases + attack scripts |
| M4 | Metrics table + SIEM export + regulatory section in memory |
| M5 | Joint demo with Daniel: upload, baseline, mutate, verify, show verdict |

## How you talk to Daniel (without blocking each other)

1. Agree on `contract_version` `0.1.0` (this folder).
2. You implement IVS in your repo; never push into his app routers.
3. When a field is missing for clinical cases, add it under `object.clinical` (open object) or propose a minor contract bump in writing (issue / short mail) before breaking JSON.
4. Joint demo day: he sets `INTEGRITY_API_BASE_URL` to your service; no code merge required if the contract holds.

## Out of scope for you

Tenant credits, OTP mail, WooCommerce, Grafana dashboards for his SaaS, Linux VM provisioning.
