> Monorepo package `api/` in `cesar-andress/hospital-transfer-integrity`.  
> Boundary: [`../docs/architecture/BOUNDARY.md`](../docs/architecture/BOUNDARY.md).  
> Scope map: [`../docs/project/ALESSA_SCOPE.md`](../docs/project/ALESSA_SCOPE.md).  
> Start here: [`../docs/GETTING_STARTED.md`](../docs/GETTING_STARTED.md).

# Integrity Verification Service (IVS)

TFG of **Alessa Renata Comparini Ceroni** (`Alcompar77`).

Verifies integrity of clinical data (health records and medical images) after a cyberattack, against a cryptographic trust baseline. Produces verdicts and reports; synthetic EHR/imaging cases; optional insider case; metrics and a short regulatory analysis.

Daniel’s SaaS (`saas/`) is only an HTTP caller. No shared database.

## Status

| Milestone | State |
|-----------|--------|
| M0 health + contract | Done |
| M1 sha256 baseline / verify / report | Done (make durable in issue A1) |
| M2 signatures | Todo — `TODO(m2)` tests |
| M3 EHR/imaging + attacks | Todo — `TODO(m3)` |
| M4 metrics + SIEM + regulatory | Todo — `TODO(m4)` |
| M5 joint demo | Todo — `TODO(m5)` / issues J* |

## Quick start

```bash
cd api
make install
make test
make run
curl -s http://localhost:8090/v1/health
```

Expect many `xfail` rows for M2–M5. M0/M1 must stay green.

## Authorship

Student TFG: Alessa Renata Comparini Ceroni.  
Tutor scaffold: César Andrés.
