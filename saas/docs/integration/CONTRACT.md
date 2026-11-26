# Integrity API contract (v0.1)

Shared by Daniel (caller) and Alessa (callee). Machine-readable twin: [`openapi-integrity.yaml`](openapi-integrity.yaml).

Base URL (Daniel config): `INTEGRITY_API_BASE_URL`  
Default in compose: `http://integrity-stub:8090`

Auth for demos: shared header `X-Integrity-Token: <INTEGRITY_SHARED_TOKEN>` (optional; stub accepts anything / empty).

## Resources

### `POST /v1/baselines`

Register a trust baseline when a file (or clinical record payload) is first accepted.

Request

```json
{
  "contract_version": "0.1.0",
  "tenant_id": "tenant_a",
  "object": {
    "kind": "file",
    "transfer_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "historia_sintetica.pdf",
    "media_type": "application/pdf",
    "size_bytes": 12345,
    "sha256": "…"
  },
  "context": {
    "source": "mvp-saas-upload",
    "case": "ehr_document"
  }
}
```

`object.kind` for Alessa's TFG will also include `ehr_record` and `dicom_study` (optional fields under `object.clinical`, see OpenAPI). Daniel's MVP may only send `kind=file` + hash.

Response (Alessa target)

```json
{
  "contract_version": "0.1.0",
  "baseline_id": "bl_…",
  "status": "registered",
  "algorithm": "sha256+ed25519",
  "registered_at": "2026-11-24T10:00:00Z"
}
```

Stub behaviour: echo request under `echo`, invent `baseline_id`, `status=passthrough`.

### `POST /v1/verifications`

Verify an object against a baseline (post-incident / on-demand).

Request

```json
{
  "contract_version": "0.1.0",
  "tenant_id": "tenant_a",
  "baseline_id": "bl_…",
  "object": {
    "kind": "file",
    "transfer_id": "550e8400-e29b-41d4-a716-446655440000",
    "sha256": "…"
  },
  "context": {
    "reason": "post_incident_check",
    "incident_id": "sim-ransom-001"
  }
}
```

Response (Alessa target)

```json
{
  "contract_version": "0.1.0",
  "verification_id": "vr_…",
  "baseline_id": "bl_…",
  "verdict": "intact",
  "detail": {
    "hash_match": true,
    "signature_valid": true,
    "notes": []
  },
  "checked_at": "2026-11-24T11:00:00Z"
}
```

`verdict` enum (Alessa fills meaning): `intact` | `altered` | `encrypted_or_unreadable` | `unknown` | `passthrough`.

Stub behaviour: `verdict=passthrough`, echo body.

### `GET /v1/health`

`{"status":"ok","service":"integrity-stub"|"ivs","contract_version":"0.1.0"}`

### `GET /v1/reports/{verification_id}` (Alessa-owned; stub 501)

Human/SIEM-oriented report. Daniel may ignore until Alessa ships it.

## Sequence (happy path)

```text
Tenant user                Daniel API              IVS (Alessa / stub)
    |  upload file              |                        |
    |-------------------------->|                        |
    |                           |  POST /v1/baselines    |
    |                           |----------------------->|
    |                           |  baseline_id           |
    |                           |<-----------------------|
    |                           |  store transfer + audit|
    |  OTP link / credits       |                        |
    |<--------------------------|                        |

Later / drill:
    |                           |  POST /v1/verifications|
    |                           |----------------------->|
    |                           |  verdict               |
    |                           |<-----------------------|
```

## Failure policy (Daniel)

| IVS result | Daniel default (configurable later) |
|------------|-------------------------------------|
| timeout / 5xx | log + continue upload (`integrity=degraded`); do not block demo |
| 4xx validation | log; treat as soft-fail in MVP |
| `verdict=altered` | record in `audit_logs`; product policy TBD (block download vs warn) |

MVP stub never blocks the transfer path.
