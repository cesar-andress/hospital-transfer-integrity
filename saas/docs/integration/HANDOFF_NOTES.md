# Tutor handoff notes (copy/adapt to mail)

## To both

You share an HTTP contract (`docs/integration/` in Daniel’s fork). You do **not** share a git repo or a database. Demo story: hospital tenant uploads via Daniel’s SaaS → integrity baseline/verify via Alessa’s service.

## To Daniel

1. Merge the English README / NEXT PR, then this integration branch.
2. Keep coding path guards and credits as your main work (`docs/NEXT.md`).
3. Compose already runs `integrity-stub`. Uploads soft-call it. When Alessa gives you a URL, only change env vars (`DANIEL_HOOK.md`).

## To Alessa Renata Comparini Ceroni

You build the **cyber / integrity** TFG (PDF proposal: clinical integrity after cyberattack). Daniel will not implement that logic.

1. Own repo (not `MVP-Saas`).
2. Copy `CONTRACT.md` + `openapi-integrity.yaml` + `ALESSA_WORKPLAN.md`.
3. Replace the echo stub with real baselines, verify, reports, synthetic EHR/imaging, attack sims, metrics, SIEM export, regulatory section.
4. Contract changes via `object.clinical` or a version bump — never by editing Daniel’s routers.
