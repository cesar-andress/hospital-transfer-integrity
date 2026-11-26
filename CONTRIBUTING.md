# Contributing (students)

Canonical repo: `cesar-andress/hospital-transfer-integrity` (public).

1. Fork the repo and clone your fork.
2. Branch from `main` (`feat/…`, `fix/…`).
3. Touch primarily `saas/` or `api/` (see [`docs/architecture/BOUNDARY.md`](docs/architecture/BOUNDARY.md)).
4. Keep commits and PR text in English.
5. Run the relevant tests before opening a PR.
6. Open a PR into `cesar-andress/hospital-transfer-integrity:main`.
7. Link the GitHub Issue / milestone.

Do not put local agent/IDE policy into tracked files. Do not weaken git hooks with `--no-verify`.

## Layout

```text
saas/     Daniel - multi-tenant transfer SaaS
api/      Alessa - Integrity Verification Service (IVS)
docs/     Shared architecture + canonical HTTP contract
```
