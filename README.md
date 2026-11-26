# hospital-transfer-integrity

Public **monorepo** for two coordinated TFGs under one hospital demo story.

| Package | Student | Role |
|---------|---------|------|
| [`saas/`](saas/) | **Daniel** (`dani84mol`) | Multi-tenant secure file-transfer SaaS (tenants, FS/“VM”, OTP, credits, Woo…) |
| [`api/`](api/) | **Alessa Renata Comparini Ceroni** (`Alcompar77`) | Integrity Verification Service — clinical integrity after cyberattack (EHR + imaging) |

**Tutor / canonical owner:** [cesar-andress](https://github.com/cesar-andress).  
Students **fork this repo** and open PRs into `main`. Legacy personal repos remain historical; this tree is the source of truth going forward.

## Read first (boundary)

The integration wall is defined once here — do not reinvent it in chat:

→ **[`docs/architecture/BOUNDARY.md`](docs/architecture/BOUNDARY.md)**  
→ Canonical HTTP contract: [`docs/contract/`](docs/contract/)  
→ Calendar: [`docs/ROADMAP.md`](docs/ROADMAP.md) (MVP **2026-12-19**, complete **2027-05-15**)  
→ PR process: [`CONTRIBUTING.md`](CONTRIBUTING.md)

```text
Daniel saas/  ──HTTP JSON contract 0.1.0──►  Alessa api/
   caller                                      callee
   own DB                                      own DB
```

## Layout

```text
hospital-transfer-integrity/
  saas/                 # Transfer SaaS (Daniel)
  api/                  # IVS (Alessa)
  docs/
    architecture/       # BOUNDARY (authoritative)
    contract/           # OpenAPI + CONTRACT (single weld)
    ROADMAP.md
  CONTRIBUTING.md
  Makefile
```

## Quick tests

```bash
# IVS (Alessa)
cd api && python3.12 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && make test

# SaaS (Daniel) — see saas/README.md / Makefile (needs its own venv/DB as documented there)
cd saas && make test
```

From repo root: `make test-api` (and `make test-saas` when the SaaS toolchain is ready).

## Status snapshot

| Area | State |
|------|--------|
| `saas/` | Living product + acceptance xfails; path-guards are the near-term MVP gate |
| `api/` | M0/M1 skeleton (sha256 baselines/verify/report) + xfails for M2–M5 |
| Joint | Contract `0.1.0`; wire compose URL to `api/` for December MVP |

## Authorship

Scaffold and architecture: César Andrés.  
TFG implementation: Daniel (`saas/`), Alessa Renata Comparini Ceroni (`api/`), via forks and PRs.
