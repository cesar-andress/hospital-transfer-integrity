> Monorepo note. This package lives in `cesar-andress/hospital-transfer-integrity` under `api/`. Canonical boundary: [`../docs/architecture/BOUNDARY.md`](../docs/architecture/BOUNDARY.md). Fork the monorepo and open PRs to `main`.

# saas-integrity-api: Clinical Integrity Verification Service (IVS)

TFG of Alessa Renata Comparini Ceroni (`Alcompar77`).

Prototype that verifies integrity of clinical data (health records and medical images) after a cyberattack (e.g. ransomware-like encryption), against a cryptographic trust baseline. Integrates conceptually with SOC/SIEM-style detection; produces verdicts and reports; evaluates synthetic EHR and imaging cases; optional insider-modification case; metrics and a short regulatory analysis.

| Role | GitHub |
|------|--------|
| Upstream (student) | [Alcompar77/saas-integrity-api](https://github.com/Alcompar77/saas-integrity-api) |
| Tutor fork | [cesar-andress/saas-integrity-api](https://github.com/cesar-andress/saas-integrity-api) |
| Caller SaaS (Daniel) | [dani84mol/MVP-Saas](https://github.com/dani84mol/MVP-Saas) |

## Boundary with Daniel (read this first)

Two TFGs. Two repos. HTTP only. No shared DB.

Daniel's multi-tenant transfer SaaS calls this service (`POST /v1/baselines`, `POST /v1/verifications`). You never implement OTP, credits, WooCommerce or his storage path guards. He never implements your signatures, clinical parsers, attack harness or SIEM export.

Full wall: [`docs/BOUNDARY.md`](docs/BOUNDARY.md), planning: [`docs/PLANNING.md`](docs/PLANNING.md), this week: [`docs/NEXT.md`](docs/NEXT.md), contract: [`docs/CONTRACT.md`](docs/CONTRACT.md).

## Status

| Milestone | State |
|-----------|--------|
| M0 health + contract in-repo | Done (this scaffold) |
| M1 sha256 baseline + verify + basic report | Done (in-memory) |
| M2 signatures | Todo, see `TODO(m2)` tests |
| M3 EHR/imaging + attacks | Todo, `TODO(m3)` |
| M4 metrics + SIEM + regulatory | Todo, `TODO(m4)` |
| M5 joint demo with Daniel | Todo, `TODO(m5)` |

## Quick start

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
make test
make run
curl -s http://localhost:8090/v1/health
```

## Authorship

Student TFG: Alessa Renata Comparini Ceroni.  
Tutor scaffolding PRs: César Andrés (`cesar-andress`).
