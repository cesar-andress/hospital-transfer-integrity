# Boundary: Daniel (MVP-Saas) and Alessa (this IVS)

Two TFGs. Two repositories. One HTTP contract. No shared database.

```
Daniel  MVP-Saas  --POST /v1/baselines|verifications-->  Alessa  saas-integrity-api (IVS)
        (caller)  <-------- verdict / report ids ------  (callee)
```

| | Daniel | Alessa (you) |
|--|--------|--------------|
| Repo | `dani84mol/MVP-Saas` | `Alcompar77/saas-integrity-api` |
| Owns | Tenants, storage/"VM", OTP, credits, Woo, front | Baselines, verify, reports, synthetic EHR/imaging, attack sims, metrics, SIEM-shaped export, regulatory note |
| Must not own | Crypto IVS guts, DICOM/EHR analysis, ransomware harness | OTP, quotas, Woo, Host routing, credit ledger |

Collaboration rule: change the contract together (`x-contract-version`); implement only on your side of the wall. Daniel points `INTEGRITY_API_BASE_URL` at this service when you are ready, no code merge required.

See also [`PLANNING.md`](PLANNING.md), [`CONTRACT.md`](CONTRACT.md), [`NEXT.md`](NEXT.md).
