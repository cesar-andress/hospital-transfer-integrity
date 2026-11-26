# Product spec (executable)

This document is the short product spec for the multi-tenant secure file-transfer SaaS.
Every rule below is encoded in `backend/tests/` so the suite is a living spec:

- a passing test = behaviour that exists today;
- an `xfail` test = target behaviour that is not built yet (the reason string says what is missing).
  `xfail_strict = true`, so when a feature is implemented its test turns into a failure
  (XPASS) until the `xfail` marker is removed.

## Actors

| Actor | Description |
|-------|-------------|
| SuperAdmin | Platform operator. Creates/deletes tenants, sees all tenants. |
| Tenant | Customer organization. Owns one storage root (its "VM filesystem"). |
| Tenant user | One of N accounts of a tenant (`max_accounts`). All users share the tenant's files. |
| Recipient | External person receiving an OTP download link. No account. |

## Requirements

### R1 - One VM filesystem per tenant, N users per tenant
- A tenant has exactly one storage root (`tenants.vm_storage_path`); users have none of their own.
- Roots are siblings under `STORAGE_BASE_PATH`; ids such as `acme` / `acme_2` never nest or collide.
- Upload, list and delete are always scoped to the caller's tenant. Cross-tenant delete is a 404 and the file survives.
- Deleting a tenant purges only that tenant's root.
- A deactivated/deleted tenant loses access immediately (token is re-checked on every request).
- Pending: sanitize upload filenames, re-validate stored paths stay under the base path,
  enforce `max_accounts`, allow owners to invite colleagues.
  Tests: `test_tenant_isolation.py`, `test_tenancy_model.py`.

### R2 - Provisioning from the shop (WooCommerce webhook)
- A paid order creates tenant + first user + storage root (quota 100, `max_accounts` 10) and emails activation.
- A second order for the same CIF/email upgrades the tenant (+100 credits); it never creates a second VM.
- Pings without billing email create nothing.
- Pending: webhook signature verification, no plaintext passwords (mail and DB).

### R3 - Credits on upload and download
- Each tenant has a credit balance (today: `quota_limit - COUNT(transfers)`).
- Upload consumes 1 credit (with or without recipient); with 0 credits upload is refused (402/429) and nothing hits disk.
- Pending (target): a successful OTP download consumes 1 credit; download is refused when the sender tenant has 0 credits;
  failed OTP never debits (already true); deleting a file does not refund; each debit is audited; check+debit is atomic.
  Tests: `test_credits.py`.

> Assumption to confirm with the product owner: credits are consumption events, not stock
> (so delete does not refund, and the same recipient re-downloading is a separate rule - see R4 single use).

### R4 - OTP links bound to the tenant VM
- Upload with a recipient emails a link `/download/<transfer_id>` and a 6-digit OTP; link expires in 24 h.
- The recipient redeems the OTP without logging in; wrong OTP = 401 (audited), unknown = 404, expired = 410.
- Pending: the served file must resolve inside the owning tenant's root (path guard);
  lockout after 5 failures; single-use links; hashed OTP at rest; link redeemable only on the owning tenant host.
  Tests: `test_otp_download.py`.

### R5 - Shared front end, tenant routing
- One SPA container serves every tenant; the public `/download/:transferId` route precedes the catch-all.
- Admin and tenant routes are role-guarded.
- Pending: nginx wildcard `<tenant>.app.saas.local`, forwarding the tenant to the API, login resolving the tenant
  from the Host, rejecting token/Host mismatches.
  Tests: `test_routing.py`.

### R6 - Later: real Linux VM per tenant
- Storage must go through a backend abstraction (`app.storage.get_backend(tenant_id)` with `put/open/delete/exists`)
  so the folder-based MVP can be replaced by a real VM (SSH/SFTP/agent) without touching routers.
- Pending: schema fields describing the VM (`vm_host`, `vm_backend`).

## Test layout

```text
backend/tests/
+-- conftest.py            # temp PostgreSQL, temp storage root, mail capture, API helper
+-- unit/                  # pure logic + SQL schema shape (no DB)
+-- acceptance/            # executable spec (@acceptance), DB-backed unless marked static
    +-- test_tenant_isolation.py
    +-- test_tenancy_model.py
    +-- test_credits.py
    +-- test_otp_download.py
    +-- test_routing.py
```

Markers: `acceptance`, `db` (needs PostgreSQL, auto-skipped without it), `static` (reads repo files).
Frontend: only static route-order checks live in pytest; a vitest suite is intentionally out of scope for now.
