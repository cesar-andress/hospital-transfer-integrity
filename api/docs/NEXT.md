# Next steps (for Alessa)

## Current milestone

| Field | Value |
|-------|--------|
| Now | Land M0/M1 skeleton from the tutor PR, run tests, replace in-memory store when ready |
| Clear | Every `TODO(m2)` ... `TODO(m5)` over time, start with M2 signatures |
| Do not | Implement Daniel's SaaS features here |

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
make test
make run   # http://localhost:8090/v1/health
```

Find remaining work:

```bash
rg 'TODO\(m[2-5]\)' tests/ docs/ app/ || true
```

## Ordered after M1

1. M2, sign baselines; verify signature; reject tampered signed payloads.
2. M3, synthetic EHR + DICOM (or stand-ins); attack scripts (flip / encrypt / insider edit).
3. M4, metrics on the corpus; SIEM-shaped event when verdict is not intact; regulatory note in `docs/`.
4. M5, schedule URL-swap demo with Daniel.

## Boundary reminder

You own IVS. Daniel owns transfer SaaS. Only HTTP + contract ids cross the wall, see [`BOUNDARY.md`](BOUNDARY.md).
