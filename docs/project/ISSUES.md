# Issue backlog

One section per GitHub issue. Assign after the collaborators accept the invite.

Labels: `track:saas`, `track:api`, `track:joint`, `boundary`, `mvp`, `ambitious`.

Daniel's issues (D1 to D8) follow the PR plan already agreed in `saas/README.md` (PR3 to PR7) and `saas/docs/NEXT.md`, and the requirement ids (R01 to R26) of the requirements matrix in `saas/README.md`.

## Milestone: MVP, December 2026 (due 2026-12-19)

### D1: Path guards for tenant storage (upload and OTP download)

Assignee: Daniel. Labels: `track:saas`, `mvp`. Due 2026-12-02.

Requirements R07 and R11 (path part). Spec: `saas/docs/SPEC.md`, R1 and R4.

Today an upload `title` containing `../` can escape the tenant folder, and `verify-otp` serves `transfers.file_path` without checking that it is still under that tenant's storage root. That breaks the "one isolated filesystem per company" rule.

Scope:

1. Add a small helper, for example `saas/backend/app/storage_paths.py`, with `safe_join(root, name)` and `assert_under_root(root, path)`. No `..`, no absolute paths; resolve with `realpath`.
2. Upload (`POST /api/v1/app/doc`): run the title or filename through the helper and answer 400 (not 500) for bad names.
3. Write files only under the tenant root (`vm_storage_path` or `STORAGE_BASE_PATH/<tenant_id>`). If `vm_storage_path` points outside `STORAGE_BASE_PATH`, reject it; do not trust the DB column.
4. OTP download (`POST /api/v1/app/download/{id}/verify-otp`): before `FileResponse`, resolve the stored path and require it to be under the owning tenant's root and under `STORAGE_BASE_PATH`. Otherwise 404 or 403. Reject symlinks that leave the root.
5. Remove every `TODO(path-guards)` and its `@pytest.mark.xfail` in:
   - `saas/backend/tests/unit/test_storage_paths.py`
   - `saas/backend/tests/acceptance/test_path_guards_milestone.py`
   - `saas/backend/tests/acceptance/test_tenant_isolation.py` (path guard cases)
   - `saas/backend/tests/acceptance/test_otp_download.py` (only the two path guard xfails)

Out of scope: credits, nginx Host routing, password hashing, webhook HMAC, OTP lockout, real Linux VM, Alessa's IVS.

Done when:

- [ ] `rg 'TODO\(path-guards\)' saas/` prints nothing
- [ ] `make test` is green, including the former xfails above
- [ ] Upload with title `../../etc/passwd` returns 400
- [ ] A normal upload and OTP download still work
- [ ] PR text and commits in English

### D2: Point the SaaS at the monorepo IVS

Assignee: Daniel. Labels: `track:saas`, `track:joint`, `mvp`.

Set `INTEGRITY_API_BASE_URL` to the `api/` service in `docker-compose.joint.yml`. The call on upload stays a soft call: if the IVS is down the upload still works. Document the variable in `saas/.env.example`. Do not implement anything of the IVS inside `saas/`.

### D3: `vms` table, `max_accounts` and user invites (PR3)

Assignee: Daniel. Labels: `track:saas`, `mvp`.

Requirements R04, R05 and R06.

- Migration with a `vms` table: one row per tenant (`UNIQUE tenant_id`), `kind` = `fs` or `linux`, `storage_root`, `status`.
- Owner endpoint to invite users (`/app/users`), refusing new users once the tenant reaches `max_accounts`.
- Turn the matching xfails in `test_tenancy_model.py` green.

### A1: Durable IVS store

Assignee: Alessa. Labels: `track:api`, `mvp`.

Replace the in-memory store with durable storage (SQLite is fine for the MVP, Postgres also). Baselines and verifications survive a restart. Tests cover the restart case.

### A2: IVS container and health check for the joint compose

Assignee: Alessa. Labels: `track:api`, `mvp`.

Keep `api/Dockerfile` working, document `make run` and the compose service `api:8090`. The health endpoint returns `service=ivs`.

### J1: Joint happy path script

Assignees: Daniel and Alessa. Labels: `track:joint`, `mvp`, `ambitious`.

One reproducible script under `docs/`: upload, baseline, controlled change of the file, verify. It must show `intact` before the change and `altered` after it. Uses both packages and no shared database.

### B0: Contract 0.1.0 acknowledgement

Assignees: Daniel and Alessa. Labels: `boundary`, `track:joint`, `mvp`.

Each student reads `docs/architecture/BOUNDARY.md` and `docs/contract/` and comments "ACK" on the issue. No code.

## Milestone: Depth, February 2027 (due 2027-02-27)

### D4: Credit ledger, debit on upload and download (PR4)

Assignee: Daniel. Labels: `track:saas`, `ambitious`.

Requirements R03, R12, R13, R14 and R15. Tests: `test_credits.py`.

- `credit_accounts` and `credit_ledger` tables, append-only deltas with `idempotency_key`; the balance equals `SUM(delta)` per tenant.
- Upload and download each cost 1 credit; with an empty balance the API answers 402 or 403.
- A failed OTP never debits. Deleting a file does not refund (assumption in SPEC, confirm with the tutor).
- Debit and transfer in the same transaction. A WooCommerce purchase adds credits to the same tenant.

### D5: Tenant routing by Host in nginx and the API (PR5)

Assignee: Daniel. Labels: `track:saas`, `ambitious`.

Requirement R10. Tests: `test_routing.py`.

nginx wildcard `<tenant>.app.saas.local` that passes the tenant to the API; login resolves the tenant from the Host. A `tenant_b` JWT on `alfa.app...` is rejected.

### D6: Security hardening (PR6)

Assignee: Daniel. Labels: `track:saas`.

Requirements R02, R11 (attempts), R17, R18, R19 and R20.

- Hashed passwords; no password in clear in the DB or in mails; activation without a clear password.
- WooCommerce webhook signed with HMAC and checked.
- OTP lockout after N failed attempts, single-use links.
- SuperAdmin not hard-coded.

### A3: M2 signatures on baselines

Assignee: Alessa. Labels: `track:api`, `ambitious`.

Sign baselines (for example Ed25519), verify the signature and reject tampered signed payloads.

### A4: M3 synthetic EHR and imaging corpus with attack harness

Assignee: Alessa. Labels: `track:api`, `ambitious`.

### A5: First metrics table on the synthetic corpus

Assignee: Alessa. Labels: `track:api`, `ambitious`.

### J2: Contract change drill (one additive clinical field)

Assignees: Daniel and Alessa. Labels: `boundary`, `track:joint`.

Propose one additive field under `object.clinical`, bump the patch version if needed, both sides green.

## Milestone: Complete, May 2027 (due 2027-05-15)

### D7: Real Linux VM per tenant, or a documented limit (PR7)

Assignee: Daniel. Labels: `track:saas`, `ambitious`.

Requirement R24. Needs a storage abstraction (`app.storage`) so the folder can be swapped for a VM. Create and destroy the VM, and do file I/O through the VM agent. If it does not fit in time, document the limit honestly.

### D8: Final security review and demo polish

Assignee: Daniel. Labels: `track:saas`.

### A6: M4 SIEM-style export and regulatory note

Assignee: Alessa. Labels: `track:api`, `ambitious`.

### A7: M5 insider modification case

Assignee: Alessa. Labels: `track:api`, `ambitious`.

### J3: Joint demo for the tribunal

Assignees: Daniel and Alessa. Labels: `track:joint`, `ambitious`.

A 10 to 15 minute demo: provision a tenant, upload, baseline, incident drill, verify, report and SIEM snippet, and the SaaS OTP download still working.

### J4: Evaluation pack for the thesis

Assignees: Daniel and Alessa. Labels: `track:joint`.

Fixed commands and the expected tables, for the annex of both theses.
