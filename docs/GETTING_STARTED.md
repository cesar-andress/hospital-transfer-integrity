# Getting started (both students)

Canonical repo: `cesar-andress/hospital-transfer-integrity` (public).  
Fork it, clone **your** fork, open PRs to `main`.

1. Read [`architecture/BOUNDARY.md`](architecture/BOUNDARY.md) once.  
2. Comment `ACK` on issue **B0**.  
3. Work only in your package (`saas/` or `api/`) unless the issue is `track:joint`.

## Alessa (`api/`)

```bash
cd api
make install
make test
make run
curl -s http://localhost:8090/v1/health
```

- Scope map: [`project/ALESSA_SCOPE.md`](project/ALESSA_SCOPE.md)  
- First coding issue: **A1** (durable store), then **A2**.  
- Passing + `xfail` is normal. Do not delete xfails until the feature is real.

Needs: Python **3.12** (or 3.11+), `make`, optional Docker for the image.

## Daniel (`saas/`)

```bash
cd saas
make test-unit          # no Postgres required
# Full suite (needs Postgres binaries or TEST_DATABASE_URL):
make test
# or skip DB:
TEST_SKIP_DB=1 make test-acceptance
```

Compose demo (optional for day one):

```bash
cd saas
cp .env.example .env
docker compose up --build
```

- Scope map: [`project/DANIEL_SCOPE.md`](project/DANIEL_SCOPE.md)  
- First coding issue: **D1** (path guards).  
- Hosts: see `saas/README.md` §6 (`app.saas.local`, …).

Needs: Python **3.10+** (3.12 preferred), `make`, Docker for the full stack, Postgres for acceptance tests (or `TEST_SKIP_DB=1` while iterating on unit work).

## Joint later

Issue **J1**: one script using both packages, no shared DB.  
Compose hint: root `docker-compose.joint.yml` + `INTEGRITY_API_BASE_URL` pointing at `api:8090`.

## Rules

- English commits and PR text.  
- One theme per PR.  
- Clear `TODO(...)` / `xfail` when green; `xfail_strict` fails unexpected passes.
