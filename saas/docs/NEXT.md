# Next steps (for Daniel)

You work in the monorepo package `saas/` under `cesar-andress/hospital-transfer-integrity` (fork + PRs to `main`).

**Full scope map (R01–R26 → issues D1–D8, plus Deferred):** [`../../docs/project/DANIEL_SCOPE.md`](../../docs/project/DANIEL_SCOPE.md).  
Issue texts: [`../../docs/project/ISSUES.md`](../../docs/project/ISSUES.md).  
Boundary with Alessa: [`../../docs/architecture/BOUNDARY.md`](../../docs/architecture/BOUNDARY.md).

Details: [`SPEC.md`](SPEC.md), acceptance `xfail`s under `backend/tests/acceptance/`, integrity hook in [`integration/`](integration/OVERVIEW.md).

## Current milestone

| Field | Value |
|-------|--------|
| Issue | Path guards for tenant VM storage (upload + OTP download) |
| Deadline | URGENT, Wednesday 2026-12-02 (EoD, Europe/Madrid) |
| Paste text | Local only (tutor keeps issue/PR body outside the repo) |

### Scope (must ship in one PR)

1. Helper module (e.g. `backend/app/storage_paths.py`): `safe_join` / assert path under root.
2. Upload: reject `../` and similar in `title`/filename with 400.
3. Do not trust `vm_storage_path` outside `STORAGE_BASE_PATH`.
4. OTP download: re-check resolved `file_path` under the owner tenant root before serving.
5. Clear all `TODO(path-guards)` markers and the matching `@pytest.mark.xfail`s in:
   - `backend/tests/unit/test_storage_paths.py`
   - `backend/tests/acceptance/test_path_guards_milestone.py`
   - `test_tenant_isolation.py` / `test_otp_download.py` (path-guard cases only)

Done when `rg 'TODO(path-guards)' backend/` prints nothing and `make test` is green.

Keep credits, nginx, passwords, OTP lockout, real VMs, and Alessa's IVS out of that PR.

```bash
git checkout main && git pull
rg 'TODO(path-guards)' backend/
make test
make test-spec-report
```

## After that (ordered)

1. Credits on download, `test_credits.py`
2. `max_accounts` + invite user, `test_tenancy_model.py`
3. Security basics, hash passwords, webhook HMAC, OTP lockout
4. Host routing, nginx + API, `test_routing.py`
5. Real Linux VM, last, needs `app.storage` abstraction

One theme per PR.

## Parallel track: Alessa Renata Comparini Ceroni (cyber / integrity TFG)

Alessa Renata Comparini Ceroni (Alessa) owns the whole cyber side: baselines, verify-after-incident, clinical/EHR/imaging cases, reports, SIEM-shaped events, metrics, regulatory notes. That is her TFG and her repository.

Daniel's job on that boundary:
- keep the echo stub + HTTP client;
- call `INTEGRITY_API_BASE_URL` (see `docs/integration/DANIEL_HOOK.md`);
- when Alessa deploys IVS, only change the URL/token.

Do not implement crypto, DICOM/EHR analysis, ransomware simulation, or integrity reports inside `saas/`.

## Product notes

- Credits: delete file = no refund (SPEC assumption) unless the tutor changes it.
- "VM" for now = isolated folder + path guards. Real Linux VM is the last milestone.
