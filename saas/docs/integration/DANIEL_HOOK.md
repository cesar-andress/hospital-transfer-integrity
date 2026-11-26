# Daniel: how to call Alessa's integrity service

You keep building the transfer SaaS ([`docs/NEXT.md`](../NEXT.md)). Integrity is not your thesis core; you only call a remote API.

## What already exists in this repo

| Piece | Role |
|-------|------|
| `services/integrity-stub/` | Tiny echo server (same paths as the contract). |
| `backend/app/integrity_client.py` | HTTP client + local fallback. |
| Compose service `integrity-stub` | Started with the stack. |
| Env `INTEGRITY_API_BASE_URL` | Default `http://integrity-stub:8090`. If it is empty or unreachable the call soft-fails and the upload continues. |
| Env `INTEGRITY_ENABLED` | `true`/`false`, kill switch. |
| Env `INTEGRITY_SHARED_TOKEN` | Sent as `X-Integrity-Token`. |

On successful upload (when enabled), the API registers a baseline with the stub/IVS and writes an audit line. It must not break uploads if IVS is down.

## What you do next (your side only)

1. Merge the English README / `NEXT.md` PR if not already on `main`.
2. Keep path-guards / credits work as your main PRs.
3. When Alessa has a URL: set in `.env`

```bash
INTEGRITY_ENABLED=true
INTEGRITY_API_BASE_URL=http://host.docker.internal:9xxx   # her service
INTEGRITY_SHARED_TOKEN=agree-a-demo-secret
```

4. Re-run an upload; check `audit_logs` / API logs for `INTEGRITY_BASELINE_*`.
5. Optional later: admin button or script that calls `verify_transfer(...)` after a drill (helper already in the client).

## What you must not do

- Do not implement signature crypto or DICOM logic in `doc_router`.
- Do not share a database with Alessa.
- Do not block her milestones waiting on nginx/credits, contract is enough.

## Quick test of the stub

```bash
docker compose up -d integrity-stub
curl -s http://localhost:8090/v1/health
curl -s -X POST http://localhost:8090/v1/baselines \
  -H 'Content-Type: application/json' \
  -d '{"contract_version":"0.1.0","tenant_id":"tenant_a","object":{"kind":"file","sha256":"abc"}}'
```

You should see `status: passthrough` and an `echo` of the body.
