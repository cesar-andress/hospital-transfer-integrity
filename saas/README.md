> Monorepo note. This package lives in `cesar-andress/hospital-transfer-integrity` under `saas/`. Canonical boundary: [`../docs/architecture/BOUNDARY.md`](../docs/architecture/BOUNDARY.md). Fork the monorepo and open PRs to `main`.

# MVP SaaS: multi-tenant secure file transfer

Working doc for this TFG fork: what the product is, what ships today, what is still open, and how to run it.

Each company (tenant) gets one isolated "VM" (a private filesystem root today; a real Linux VM later), N users on that same VM, one shared front end, OTP download links that only read from the owning tenant's VM, and SaaS credits that should burn on upload and download. WooCommerce provisions tenants; Prometheus/Grafana cover basic observability.

| Role | GitHub |
|------|--------|
| Fork / technical tutoring | [cesar-andress](https://github.com/cesar-andress) |
| Upstream (student) | [dani84mol/MVP-Saas](https://github.com/dani84mol/MVP-Saas) |
| This fork | [cesar-andress/MVP-Saas](https://github.com/cesar-andress/MVP-Saas) |

Demo passwords are plaintext on purpose. Do not run this stack as-is outside a lab (see [§8](#8-security-demo-vs-production)).

---

## Contents

1. [Product vision](#1-product-vision)
2. [Architecture: today vs target](#2-architecture-today-vs-target)
3. [Timeline](#3-timeline)
4. [Requirements matrix](#4-requirements-matrix)
5. [PR plan](#5-pr-plan)
6. [Getting started](#6-getting-started)
7. [Target data model](#7-target-data-model)
8. [Security: demo vs production](#8-security-demo-vs-production)
9. [Authorship](#9-authorship)
10. [Glossary](#10-glossary)
11. [Appendix](#11-appendix)

Status labels used below:

| Label | Meaning |
|-------|---------|
| Done | In `main` (or documented as finished). |
| In progress | Branch / open work, not finished. |
| Todo | Planned, no code yet. |
| Deferred | Known, out of TFG scope for now. |

All docs, comments, and commit messages in this fork stay in English.

---

## 1. Product vision

### 1.1 What it is

A company signs up (WooCommerce or SuperAdmin), gets an isolated environment, and its staff send files to outsiders with expiry and an audit trail. The recipient opens a link, types an OTP, and downloads, no account required.

### 1.2 Product rules

1. Sign-up. Woo webhook or SuperAdmin. A second purchase for the same CIF/email tops up the plan; it never creates a second VM.
2. One VM per company. Today: directory under `STORAGE_BASE_PATH` (`tenants.vm_storage_path`). End state: real Linux VM per tenant ([PR7](#5-pr-plan)).
3. N users, one VM. Everyone in the tenant shares that storage. Cap is `max_accounts`. No per-user disks.
4. Shared front. One React/Vite SPA. Isolation comes from login (`tenant_id` in the JWT) and, later, nginx Host routing ([PR5](#5-pr-plan)).
5. OTP links stay inside the owner VM. A transfer id from tenant A must never serve bytes from tenant B, or escape A's storage root.
6. Credits. Burn on upload and download. Today we only cap stored transfer count on upload; a real ledger is [PR4](#5-pr-plan).
7. WooCommerce. Sells plans; webhook creates tenant + owner + VM, or tops up an existing one.
8. Observability. Prometheus + Grafana (HTTP metrics and per-tenant quota leftovers).

### 1.3 Actors

| Actor | Role |
|-------|------|
| SuperAdmin | Creates / disables / purges tenants, monitoring. Demo: hard-coded login. |
| Tenant owner | First user at provision time; should invite peers up to `max_accounts`. |
| Tenant user | Uploads files, creates OTP links. |
| External recipient | Gets email + OTP; no account. |
| Shop (WooCommerce) | Triggers provision / top-up via webhook. |

### 1.4 End-to-end flow (target)

```text
 1. Company buys a plan on tienda.saas.local
 2. Signed webhook -> API creates tenant + owner + VM
 3. Activation mail with set-password link (no cleartext password)
 4. Owner logs into the shared SPA -> JWT {tenant_id, role}
 5. Owner invites users (≤ max_accounts); all share the VM
 6. User uploads -> bytes only under that VM -> −1 credit
 7. API builds transfer + OTP + expiry -> mail to recipient
 8. Recipient opens link -> OTP -> read only from owner VM -> −1 credit -> audit_logs
 9. Grafana shows usage / remaining credits per tenant
10. Same company buys again -> more credits, same VM
```

---

## 2. Architecture: today vs target

### 2.1 Today (`main`)

```text
                       +-----------------------+
   *.saas.local -----> |  Nginx (by service)   |   not by tenant
                       +-----------+-----------+
        +---------------+----------+---------------+---------------+
        v               v          v               v               v
   app.saas.local  api.saas.local  shop         grafana         mail
   SPA :5173       FastAPI :8001   WP+Woo       :3000           MailHog
                       |
      +----------------+----------------------+
      v                v                      v
  PostgreSQL        SMTP sink            vm_storage/
  tenants,users,                         +-- tenant_a/   <- "VM" = folder
  transfers,                             +-- <tenant_id>/
  audit_logs
```

What that means in practice:

- One API process writes local disk; "VM" = `vm_storage/<tenant_id>/`.
- Isolation = JWT `tenant_id` + SQL filters + that folder.
- Login asks for `tenant_id` (plus demo `admin`).
- Quota = row count in `transfers`; checked on upload only.
- 6-digit OTP, 24h expiry, public verify endpoint.
- Woo webhook is open; activation mail ships the password in cleartext.
- Nginx routes `app` / `api` / `tienda` / `grafana` / `mail`, not per company.

### 2.2 Target

```text
  alfa.app.saas.local -+
  beta.app.saas.local -+-> nginx (TLS, host->tenant, rate limits)
  api.saas.local ------+         |
                                 v
                    Shared SPA + API
                    JWT tenant must match Host
                    credit ledger; path guards
                         |
            +------------+------------+
            v                         v
       PostgreSQL              VM orchestrator
       tenants, vms,           +-- one Linux VM / tenant
       users, credits,             (file agent: put/get/delete)
       transfers, audit
```

### 2.3 Gap summary

| Layer | Today | Missing |
|-------|-------|---------|
| Provisioning | Admin + Woo create tenant/owner/dir | HMAC webhook, set-password mail, `vms` table |
| "VM" | Folder | Path guards, `vms` row, then real Linux VM |
| Users | N users in DB | Invite API, enforce `max_accounts` |
| Front | One SPA, tenant typed at login | Host-based tenant |
| Routing | nginx by service | nginx by tenant, Host == JWT |
| OTP | Code + 24h | Attempt cap, hashed OTP, strict path check |
| Credits | Transfer count on upload | Ledger; debit download too |
| Security | JWT + SQL scope | Password hash, secrets out of tree, TLS |
| Tests | Suite on `main` (`xfail` = open work) | Turn xfails green as features land |

---

## 3. Timeline

Past dates come from `git log`. Future weeks are planning guesses.

### 3.1 Done

| Date | Status | Note |
|------|--------|------|
| 2026-11-18 | Done | Student upstream: first commits (`47d42d2`, `db9341f`) |
| 2026-11-20 | Done | Product audit vs code; PR1 docs/schema/cleanup on fork (`2b68c73`) |
| 2026-11-20 | Done | PR2 test suite + docs branches prepared on the fork |
| 2026-11-23 | Done | Student merged PRs #1, #2, #3 into `dani84mol/main`; tags `v0.1.0`-`v0.1.4` |
| 2026-11-23 | Done | Follow-up commit on upstream README (left merge conflict markers, fixed in this branch) |
| 2026-11-24 | In progress | English README rewrite + sync fork `main` with upstream |

### 3.2 Next (proposed)

| Window | Status | Work | PR |
|--------|--------|------|----|
| 2026-11-24 | In progress | English docs; clear leftover merge junk | this branch |
| 2026-11-30 to 12-11 | Todo | FS guards + `vms` table + `max_accounts` | PR3 |
| 2026-12-14 to 12-23 | Todo | Credit ledger; debit upload and download | PR4 |
| 2027-01-11 to 01-22 | Todo | Tenant Host routing in nginx | PR5 |
| 2027-01-25 to 02-12 | Todo | Password hash, webhook HMAC, OTP lockout | PR6 |
| 2027-02-15 to 03-26 | Todo | Real Linux VM per tenant | PR7 |
| Later | Deferred | Byte quotas, fancy billing, HA, managed TLS | - |

```text
PR1 docs -> PR2 tests -> PR3 FS/vms -> PR4 credits -> PR5 routing -> PR6 security -> PR7 Linux VM
 (merged)   (merged)     ^_____________________ enables real VM swap _________________^
```

---

## 4. Requirements matrix

Audit of 2026-11-20, updated after the Nov 23 merges. "Test" = acceptance suite / `xfail` where noted.

| # | Requirement | Status | Gap | PR |
|---|-------------|--------|-----|----|
| R01 | Admin can create companies | Done | - | - |
| R02 | Woo auto-provision | Done (demo) | No signature | PR6 |
| R03 | Second purchase tops up same CIF | Done | Still bumps `quota_limit`, not a ledger | PR4 |
| R04 | One VM per tenant | Done as FS | No `vms` table | PR3 / PR7 |
| R05 | N users, one VM | Partial | No invite API / `max_accounts` check | PR3 |
| R06 | Owner invites peers | Todo | No `/app/users` | PR3 |
| R07 | FS isolation | Partial | Need path sanitize + base-path check | PR3 |
| R08 | Shared front | Done | - | - |
| R09 | Login isolation (JWT tenant) | Done | - | - |
| R10 | nginx Host isolation | Todo | Service Hosts only | PR5 |
| R11 | OTP only against owner VM | Partial | Need path guard + attempt limits | PR3 / PR6 |
| R12 | Credits on upload | Partial | Count-based quota | PR4 |
| R13 | Credits on download | Todo | Download is free today | PR4 |
| R14 | Auditable credit ledger | Todo | - | PR4 |
| R15 | Woo tops up credits | Todo | - | PR4 |
| R16 | Prometheus / Grafana | Done (base) | Credit/VM metrics later | PR4 / PR7 |
| R17 | Password hashing | Todo | Plaintext in DB | PR6 |
| R18 | Activation without cleartext password | Todo | - | PR6 |
| R19 | Signed webhook | Todo | - | PR6 |
| R20 | SuperAdmin not hard-coded | Todo | - | PR6 |
| R21 | `audit_logs` | Done (base) | Broader coverage later | PR4 / PR6 |
| R22 | Automated tests | Done | Suite on `main`; many `xfail` | - |
| R23 | Product docs | Done | Keep English | - |
| R24 | Real Linux VM | Todo | Folder only | PR7 |
| R25 | Byte quotas | Deferred | - | - |
| R26 | Managed TLS / custom domains | Deferred | - | - |

Executable detail: [`docs/SPEC.md`](docs/SPEC.md).  
What to do this week: [`docs/NEXT.md`](docs/NEXT.md).  
Split with the integrity TFG (Alessa Renata Comparini Ceroni): [`docs/integration/OVERVIEW.md`](docs/integration/OVERVIEW.md).

---

## 5. PR plan

Small PRs, one theme each.

| PR | Theme | Status |
|----|-------|--------|
| #1 | Docs / `init_db` fix / dead code | Merged upstream 2026-11-23 |
| #2 | Large README + roadmap | Merged (was Spanish, this branch puts it in English) |
| #3 | Pytest living spec | Merged |
| PR3 | FS guards + `vms` + invites / `max_accounts` | Todo |
| PR4 | Credits ledger (upload + download) | Todo |
| PR5 | Tenant Host routing | Todo |
| PR6 | Security hardening | Todo |
| PR7 | Real Linux VM | Todo |

Acceptance hints:

- PR3: path-traversal xfails go green; `vms` migration exists.
- PR4: upload and download each cost 1 credit; empty balance returns 402/403; ledger matches balance.
- PR5: `alfa.app…` with a `tenant_b` JWT is rejected.
- PR6: hashed passwords, signed webhook, no password in mail.
- PR7: create/destroy VM; I/O via the VM agent.

---

## 6. Getting started

### 6.1 URLs

| Service | URL | Notes |
|---------|-----|-------|
| Front | `http://app.saas.local` | Admin + tenant + OTP download |
| API | `http://api.saas.local` | `/api/v1`, `/docs`, `/metrics` |
| Shop | `http://tienda.saas.local` | WordPress + Woo |
| Grafana | `http://grafana.saas.local` | `admin` / `admin` |
| MailHog | `http://mail.saas.local` | Captured mail |
| Postgres | `localhost:5432` | `saas_db` / `postgres` / `postgres` |

```text
127.0.0.1 app.saas.local api.saas.local tienda.saas.local grafana.saas.local mail.saas.local
```

### 6.2 Docker Compose

```bash
# From the monorepo checkout (fork of cesar-andress/hospital-transfer-integrity)
cd saas
cp .env.example .env
docker compose up --build
```

Open `http://app.saas.local` (or `:5173`).

```bash
docker compose down       # keep volumes
docker compose down -v    # wipe DB + demo data
```

### 6.3 Demo logins

| Role | Tenant | Email | Password |
|------|--------|-------|----------|
| SuperAdmin | `admin` | `admin@saas.com` | `adminpassword` |
| Alfa | `tenant_a` | `user1@alfa.com` | `password123` |
| Alfa #2 | `tenant_a` | `user2@alfa.com` | `password123` |
| Beta | `tenant_b` | `user1@beta.com` | `password123` |
| Beta #2 | `tenant_b` | `user2@beta.com` | `password123` |

`tenant_b` has a tiny quota so you can hit the limit quickly.

### 6.4 Smoke flow

1. Login as Alfa, upload with a recipient.
2. Open MailHog, grab link + OTP.
3. Download in another window.
4. Login as the other Alfa user, same files (same VM).
5. Login as Beta, no Alfa files.
6. SuperAdmin: create a tenant; check `vm_storage/`.

### 6.5 Env

See [`.env.example`](.env.example). Change `SECRET_KEY` outside demo.

### 6.6 Git

Canonical monorepo: `cesar-andress/hospital-transfer-integrity`.  
Fork it, clone your fork, open PRs to `main`. Work under `saas/`.  
Scope map: [`../docs/project/DANIEL_SCOPE.md`](../docs/project/DANIEL_SCOPE.md).  
Getting started: [`../docs/GETTING_STARTED.md`](../docs/GETTING_STARTED.md).

### 6.7 Tests

Passing tests = behaviour that exists. `xfail` = not built yet (`xfail_strict` is on).

```bash
make test
make test-unit
make test-acceptance
make test-spec-report
```

Or:

```bash
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
.venv/bin/python -m pytest tests/unit
.venv/bin/python -m pytest -m acceptance -rxX
```

- DB: `TEST_DATABASE_URL`, or a throwaway Postgres via `initdb`/`pg_ctl`. `TEST_SKIP_DB=1` skips DB tests. Storage uses a temp dir, never real `vm_storage/`.
- Front: static route-order checks in pytest only.
- Needs Python 3.10+ locally (image is 3.12).

---

## 7. Target data model

### 7.1 Now (`backend/scripts/init_db.sql`)

`tenants`, `users`, `transfers`, `audit_logs`. VM path lives on `tenants.vm_storage_path`. `quota_limit` counts transfers.

### 7.2 Target shape

```text
 tenants 1---1 vms
    |---N users
    |---1 credit_accounts 1---N credit_ledger
    |---N transfers
    +---N audit_logs
```

`vms`: one row per tenant (`UNIQUE tenant_id`), `kind` = `fs` | `linux`, `storage_root` or host/agent fields, `status`.

`credit_accounts` / `credit_ledger`: balance + append-only deltas (`upload`, `download`, `purchase`, ...) with `idempotency_key`. Balance must equal `SUM(delta)` per tenant; debit in the same transaction as the transfer/download.

`transfers`: store a path relative to the VM root (`file_key`), hashed OTP, attempt counter, never a raw host absolute path from the client.

`users`: `password_hash`, roles `owner` | `user`, enforce `max_accounts` on insert.

### 7.3 Hard rules

- Exactly one `vms` row per tenant.
- Resolved file paths must stay under that VM root.
- Credit checks use `SELECT … FOR UPDATE` (or equivalent) before debit.

---

## 8. Security: demo vs production

### 8.1 Demo-only shortcuts

| Item | Demo | Production |
|------|------|------------|
| User passwords | Plaintext | Argon2/bcrypt |
| SuperAdmin | Hard-coded | DB / IdP + MFA |
| JWT `SECRET_KEY` | Default string | Real secret store |
| Woo webhook | Open | HMAC |
| Activation mail | Includes password | One-time set-password link |
| OTP | Cleartext, no lockout | Hash + attempts + rate limit |
| Transport | HTTP | TLS |
| `/metrics`, Grafana | Open | Private network / auth |

### 8.2 Non-negotiable even in demo

1. No cross-tenant read/list/delete/download. Scope from JWT `tenant_id`, never from a client-supplied id alone.
2. No filesystem escape outside the tenant VM root.
3. No real secrets in git (`.env` ignored; `.env.example` only).
4. A disabled tenant loses access immediately.
5. OTP downloads only serve the owning tenant's VM.

### 8.3 Before any real deploy

- [ ] Password hashing + set-password flow  
- [ ] SuperAdmin out of source  
- [ ] Secrets in a vault  
- [ ] Webhook HMAC  
- [ ] TLS + security headers  
- [ ] Hashed OTP + lockout  
- [ ] Metrics/Grafana not public  
- [ ] Backups for DB and VMs  
- [ ] Protected audit logs  

---

## 9. Authorship

- Fork maintainer: César Andrés `<cesar.andress@ucjc.edu>` / [cesar-andress](https://github.com/cesar-andress).
- Upstream: [dani84mol](https://github.com/dani84mol).
- The exam board does not grade GitHub history; tutoring commits on this fork are fine.
- English for docs, comments, and commit messages.

See [`AUTHORS.md`](AUTHORS.md).

---

## 10. Glossary

| Term | Meaning |
|------|---------|
| Tenant | Customer company (`tenant_id`, `cif_nif`). |
| VM | Tenant runtime + storage. Now = isolated folder. Later = Linux VM (PR7). |
| Shared front | One SPA for every tenant. |
| Host routing | nginx picks tenant from hostname (PR5). |
| OTP link | Download URL + code; must resolve inside owner VM. |
| Credit | Consumed on upload and download. |
| Ledger | Append-only credit movements. |
| Quota (current) | Max stored transfers (`quota_limit`); precursor to credits. |
| Living spec / `xfail` | Acceptance test for a missing feature. |
| upstream / origin | Student repo / this fork. |

---

## 11. Appendix

### 11.1 Layout

```text
MVP-Saas/
+-- docker-compose.yml
+-- nginx.conf
+-- Makefile
+-- .env.example
+-- AUTHORS.md
+-- docs/SPEC.md
+-- backend/
|   +-- scripts/init_db.sql
|   +-- tests/                 # unit + acceptance
|   +-- app/                   # FastAPI
+-- frontend/src/              # Vite SPA
```

### 11.2 API surface

| Prefix | Auth | Job |
|--------|------|-----|
| `/api/v1/auth` | Public login | JWT |
| `/api/v1/admin` | Admin JWT | Tenants CRUD + purge |
| `/api/v1/app` | Tenant JWT (+ public OTP) | Upload / list / delete / OTP download |
| `/api/v1/webhooks` | Public (demo) | Woo provision / resend |
| `/metrics` | Public | Prometheus |

Interactive docs: `http://api.saas.local/docs`

### 11.3 Contributing

- Start from [`docs/NEXT.md`](docs/NEXT.md).
- One theme per PR.
- Prefer flipping an `xfail` when you ship a feature.
- Quota today counts files stored, not bytes.

### 11.4 License

Same as upstream unless the original owner says otherwise.
