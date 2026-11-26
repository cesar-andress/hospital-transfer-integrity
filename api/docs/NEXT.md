# Next steps (for Alessa)

Work in monorepo package `api/`. Fork `cesar-andress/hospital-transfer-integrity`, PRs to `main`.

| Doc | Link |
|-----|------|
| Full scope | [`../../docs/project/ALESSA_SCOPE.md`](../../docs/project/ALESSA_SCOPE.md) |
| Issues | [`../../docs/project/ISSUES.md`](../../docs/project/ISSUES.md) |
| Getting started | [`../../docs/GETTING_STARTED.md`](../../docs/GETTING_STARTED.md) |
| Boundary | [`../../docs/architecture/BOUNDARY.md`](../../docs/architecture/BOUNDARY.md) |

## Now (MVP)

1. **A1** durable store (replace memory).  
2. **A2** container + health for joint compose.  
3. **B0** ACK boundary.  
4. **J1** with Daniel when both sides ready.

```bash
cd api && make install && make test && make run
```

## After MVP (ordered)

1. **A3** signatures (`TODO(m2)`).  
2. **A4** EHR/imaging + attacks (`TODO(m3)`).  
3. **A5** first metrics table.  
4. **A6** SIEM + regulatory (`TODO(m4)`).  
5. **A7** insider case + **J3/J4** joint demo / evaluation pack.
