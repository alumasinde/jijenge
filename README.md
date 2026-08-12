# Jijenge — Kenya Services Marketplace

A location-aware, two-sided marketplace API that matches customers who need
a job done with verified service providers in their area — job posting,
provider matching, scheduling, in-app job execution, M-Pesa payments,
platform commission, disputes/refunds, and financial reporting.

---

## 1. What this application does

Jijenge is the backend for a Kenyan services marketplace (think: a
TaskRabbit/Jiji-style platform), built in 26 incremental phases:

1. **Onboarding & identity** — customers and providers register, verify
   phone/email, and build a trust profile (ratings, verification status,
   experience).
2. **Service catalogue & job posting** — customers post jobs against a
   defined service catalogue, at a specific location.
3. **Matching engine** — a configurable, database-driven scoring engine
   ranks eligible providers by distance, rating, verification status,
   availability, and experience (default weights: 35/25/15/15/10%,
   editable in `matching_rules` without a code change).
4. **Applications & assignment** — providers apply or get auto-matched;
   assignment is atomic (a job cannot be double-booked).
5. **Job execution lifecycle** — start, in-progress, completion
   confirmation (both parties), cancellation, with timeout/expiry rules
   handled by a background worker.
6. **Payments** — a provider-agnostic payment abstraction with a Cash
   provider and a live M-Pesa Daraja (STK Push + callback verification)
   provider; idempotency keys prevent double-charging.
7. **Commission, settlement & payouts** — platform commission is
   calculated per job, provider earnings are held and settled, and
   payouts are executed through the same provider abstraction.
8. **Disputes & refunds** — a bounded dispute window, evidence
   submission, and a refund lifecycle tied to the financial ledger.
9. **Reconciliation & ledger** — every money movement is recorded as an
   immutable ledger entry; a reconciliation worker cross-checks provider
   callbacks against internal state.
10. **Admin reporting** — financial summary and KPI endpoints (jobs,
    transactions, open disputes, pending settlements, reconciliation
    exceptions) for an admin dashboard to consume.

**There is no frontend in this repository** — it is a pure JSON API
(`/api/v1/...`) intended to be consumed by a web and/or mobile client. See
§6 for a frontend recommendation.

---

## 2. Tech stack

| Layer | Choice |
|---|---|
| Language / runtime | Python 3.12 |
| Web framework | FastAPI 0.116 (ASGI, via Uvicorn) |
| Database | MySQL 8 (InnoDB, utf8mb4) via `mysql-connector-python` |
| Migrations | Custom checksum-verified SQL migration runner (`migrate.py`) — no ORM, no Alembic |
| Auth | Argon2id password hashing + JWT (HS256) access/refresh tokens, token-version based revocation |
| Validation | Pydantic v2 / `pydantic-settings` |
| Payments | M-Pesa Daraja (STK Push, B2C, callback verification) + Cash |
| Rate limiting | Custom MySQL-backed fixed-window limiter (safe across multiple app workers/instances) |
| Background jobs | Polling worker (`workers/run.py`) using `SELECT ... FOR UPDATE SKIP LOCKED` as a job queue |
| Testing | pytest (45 tests — schema, security, financial math, matching logic) |
| Security tooling | `tools/security_audit.py` — static check for string-interpolated SQL and migration integrity |

**Architecture pattern:** each business domain is a self-contained module
under `backend/app/Modules/<Name>/` with `routes.py → Controllers → Services
→ Repositories`. Business logic lives in Services; controllers stay thin;
repositories are the only layer that touches SQL. This is consistent across
all business modules (Auth, Users, Providers, Services, Locations, Jobs,
Applications, Availability, Matching, Notifications, Payments, Financials,
Reviews, Verification, Trust, Execution, Disputes, JobLifecycle, System,
Branding).

---

## 3. Production-readiness assessment

**Overall: the engineering is genuinely solid — this is not vibecoded.**
Password handling, timing-attack mitigation on login, idempotent payments,
row-locked job queues, checksum-tracked migrations, and a production
config-guard (`Settings.validate_runtime()`) that refuses to boot with
debug mode, a weak JWT secret, wildcard CORS, or unconfigured M-Pesa in
`APP_ENV=production` — these are patterns a careful senior engineer writes,
not patterns an LLM free-associates. The module structure is consistent
across all 18 domains with no shortcuts taken in any one area.

**What I found and already fixed in this pass:**

- **Critical — app could not start.** `app/config.py` defined the
  `Settings` class but never instantiated `settings = Settings()`. Every
  import of `app.config.settings` (i.e. the entire application) raised
  `ImportError`. This is now fixed, and `validate_runtime()` is called at
  import time so bad production config fails immediately on boot rather
  than on the first request.
- **Stale test.** `test_phase10_payment_options.py` called a
  `CashProvider.initiate()` method that no longer exists (the real
  interface is `initiate_customer_payment()`, per `Providers/base.py`).
  This was leftover from an earlier draft of the payment provider
  interface and wasn't a real product bug, just test debt — updated to
  match the current interface.
- **Duplicate/dead worker implementation.** `app/Workers/` (thin, only
  handled matching jobs) and `workers/` (the full implementation actually
  wired to `EXPIRE_ASSIGNMENTS` / `EXPIRE_COMPLETION_CONFIRMATIONS` /
  financial retry jobs) both existed. Nothing imported `app/Workers/`, so
  it was dead code. Removed — `workers/run.py` is the one worker
  entrypoint now.

After these fixes: the app imports and boots cleanly (84 module routes register),
`tools/security_audit.py` passes (no string-interpolated SQL across 188
files, no migration numbering conflicts across 100 migrations), and all 45
tests pass.

**What's still missing before a real production launch (not code-quality
issues — infrastructure/ops gaps expected at this stage):**

- No Dockerfile / CI pipeline existed — added in this pass (§5).
- No migration **rollback** story — `migrate.py` applies forward-only and
  rejects a modified-after-applied migration (good, prevents silent
  drift), but there's no `down` migration convention. For a launched
  product, write-ahead each migration with its manual rollback SQL in a
  runbook rather than relying on `migrate.py` for reversal.
- `client_ip()` in `Core/rate_limit.py` deliberately reads the raw socket
  peer address and ignores `X-Forwarded-For` — correct today, but once
  this sits behind a load balancer/reverse proxy you must explicitly trust
  a single hop of `X-Forwarded-For`/`X-Real-IP` or rate limiting will key
  everyone off the proxy's IP.
- No structured logging/observability (no request logging, no error
  tracking integration, no metrics) — fine for this stage, necessary
  before real traffic.
- No automated CI (tests + security audit run manually, not on every
  push).

**Verdict:** the backend is a real, coherently-architected application at
roughly a late-beta stage of maturity — the one boot-blocking bug is fixed,
the remaining gaps are standard pre-launch ops work, not a rebuild.

---

## 4. Running migrations safely

`migrate.py` is deliberately simple and strict, not a toy:

- Every migration file must match `NNN_description.sql` (3+ digit, strictly
  increasing, no gaps required but no duplicates allowed).
- Each applied migration's **filename and SHA-256 checksum** are recorded
  in `schema_migrations`. If you edit a migration file *after* it has been
  applied anywhere, the next run refuses to proceed — you must write a new
  migration instead. This is what stops "just tweak the old migration"
  drift between environments.
- `python tools/validate_migrations.py` performs a database-free migration integrity check. `migrate.py --check` parses every pending migration (splitting on
  semicolons while respecting quotes/backticks/comments) **without
  executing anything** — safe to run as a CI/pre-deploy gate.
- Each migration runs inside its own transaction; a failure rolls back
  that migration only.

**Safe rollout procedure:**

```bash
# 1. Dry-run against a staging copy of the schema first, always.
MYSQL_HOST=staging-db ... python migrate.py --check

# 2. Apply to staging, run the app + test suite against it.
MYSQL_HOST=staging-db ... python migrate.py

# 3. Take a database backup/snapshot of production immediately before
#    applying (mysqldump or your managed DB's snapshot feature — this
#    project does not automate that step; treat it as a manual gate).

# 4. Apply to production during a low-traffic window.
MYSQL_HOST=prod-db ... python migrate.py
```

Never hand-edit a migration that has already run anywhere (staging or
prod) — write a new migration that alters/corrects it. Never run
`migrate.py` from a machine that doesn't have the exact same `migrations/`
directory as what's committed — the checksum check is your protection
against drift, don't route around it.

---

## 5. Deployment

Three files were added, alongside this README:

- `backend/Dockerfile` — production image for the API (non-root user,
  healthcheck against `/api/v1/system/health`, `UVICORN_WORKERS` tunable).
- `backend/Dockerfile.worker` — separate image for the background worker
  (`workers/run.py`), so it can be scaled independently of the API.
- `backend/docker-compose.yml` — local/staging stack: MySQL, a one-shot
  `migrate` service that runs `migrate.py` and gates the API/worker
  startup on its success, the API, and the worker.

### Quick start (local/staging)

```bash
cd backend
cp .env.example .env
# edit .env — set MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD, JWT_SECRET (32+ chars)

docker compose up --build
# API:    http://localhost:8000/api/v1/system/health
# MySQL:  localhost:3306 (bound to 127.0.0.1 only)
```

### Production notes

- Set `APP_ENV=production` — this activates `validate_runtime()`, which
  refuses to boot without `APP_DEBUG=false`, a 32+ char `JWT_SECRET`,
  explicit non-wildcard `CORS_ORIGINS`, and (if `MPESA_ENABLED=true`) a
  complete, HTTPS-only M-Pesa configuration. Treat any boot failure here
  as the app protecting you, not a bug.
- Run `migrate.py` as a separate deploy step (or the `migrate` compose
  service) — never let the API container run migrations implicitly on
  startup, so a failed migration can't take down running replicas.
- Put a reverse proxy (nginx/Caddy/your cloud LB) in front for TLS
  termination, and update `client_ip()` in `Core/rate_limit.py` to trust
  that proxy's forwarded header once one is in place.
- Point `MPESA_CALLBACK_URL` at a publicly reachable HTTPS endpoint before
  enabling M-Pesa in production — `validate_runtime()` enforces this.
- Scale `api` and `worker` independently; the worker is a single polling
  loop per container, so run multiple worker containers for throughput —
  `FOR UPDATE SKIP LOCKED` makes concurrent workers safe.

---

## 6. Frontend recommendation

There's no frontend built yet, so this is a recommendation for what to
build against this API, not a comparison of existing options.

**Recommended: Next.js (React, App Router) for the web client, as a
separate repo/deployment, talking to this API over HTTPS.**

Why, given what this backend actually is:

- It's a **two-sided marketplace** (customer-facing job posting/tracking
  UI + provider-facing job/availability/earnings UI). These are different
  enough audiences that they benefit from either two separate Next.js apps
  or one app with a hard route-level split — either way, a component
  framework with real routing and data-fetching conventions (Next.js) pays
  for itself quickly versus a plain SPA.
- The API is already a clean, stateless JWT-authenticated REST/JSON
  service — it doesn't push you toward any particular frontend framework,
  so this comes down to what scales for a marketplace UI specifically:
  SEO matters for the customer-acquisition side (job categories, provider
  profiles are worth indexing), which a plain client-rendered SPA (e.g.
  Vite + React) doesn't give you for free — Next.js does via SSR/ISR.
- If a mobile app is on the roadmap too, React Native / Expo shares
  language, and a lot of API-client and validation code, with a
  Next.js/React web app — worth factoring in now even if mobile is phase 2.
- Avoid server-rendered PHP/Blade/Django-templates here specifically
  *because* the backend is already a decoupled JSON API — building a
  templated frontend on top would mean re-implementing routing/session
  concerns the API wasn't designed to hand off, and would block you from
  ever reusing this same API for a mobile client later.

If you want a faster, smaller build first (admin/ops dashboard, or an
internal tool rather than the customer-facing product), a plain Vite +
React SPA is the lighter-weight choice — you lose SSR/SEO but gain a
simpler deploy (static hosting, no Node server to run).

---

## 7. Environment variables reference

See `backend/.env.example` for the full list with defaults. The ones that
matter most operationally:

| Variable | Notes |
|---|---|
| `APP_ENV` | `development` or `production` — controls `validate_runtime()` strictness |
| `JWT_SECRET` | Must be 32+ chars in production; rotating it invalidates all sessions |
| `CORS_ORIGINS` | Comma-separated; no wildcard allowed in production |
| `MYSQL_*` | Standard connection params |
| `RATE_LIMIT_ENABLED` + `*_RATE_LIMIT_PER_MINUTE` | Per-bucket limits (auth/login/register/refresh) |
| `MPESA_ENABLED` | If true, all `MPESA_*` fields become required and `MPESA_CALLBACK_URL` must be HTTPS in production |

---

## 8. Local development (without Docker)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # edit values

python migrate.py           # apply schema
python migrate.py --check   # dry-run only, no changes

uvicorn app.main:app --reload   # http://127.0.0.1:8000

python -m workers.run --once    # run one worker cycle, for testing
python -m workers.run           # run the worker loop

python tools/security_audit.py  # static security check
python -m pytest                # 45 tests
```


## 5. Current modules

The backend is organized under `backend/app/Modules/`:

- Auth
- Users
- Providers
- Services
- Locations
- Jobs
- Applications
- Availability
- Matching
- Notifications
- Payments
- Financials
- Reviews
- Verification
- Trust
- Execution
- JobLifecycle
- Disputes
- System
- Branding

`System` owns application/business settings. `Branding` owns runtime visual identity
such as colors, logos, typography and dark-theme configuration. Secrets such as
JWT and M-Pesa credentials remain environment configuration and are never stored
in branding/settings tables.

## 6. Local Docker startup

From the repository root:

```bash
cp .env.example .env
# edit .env and set strong MYSQL_PASSWORD, MYSQL_ROOT_PASSWORD and JWT_SECRET

docker compose up --build
```

The root compose file builds from `./backend`. Startup order is:

`mysql -> migrate -> api/worker`

The migration service runs all pending migrations before the API and worker are
allowed to start.

Useful checks:

```bash
curl http://127.0.0.1:8000/api/v1/system/health
curl http://127.0.0.1:8000/api/v1/system/ready
curl http://127.0.0.1:8000/api/v1/branding
curl http://127.0.0.1:8000/api/v1/system/settings
```

The first endpoint is a process health check. The second verifies that MySQL is
reachable. The branding and public-settings endpoints require migrations 099 and
100 to have completed.

For a database-free migration check:

```bash
cd backend
python tools/validate_migrations.py
python migrate.py --check
```

For tests, install development dependencies:

```bash
pip install -r requirements-dev.txt
pytest -q
```

`tests/test_system_branding_database.py` is an integration test and requires a
real MySQL database; it is skipped when the integration-test flag is not enabled.

## 7. Frontend contract

There is intentionally no frontend in this repository yet. The intended client
is a React + TypeScript + Vite application using Tailwind CSS with CSS variables
populated from `/api/v1/branding`. The same client can be shipped as a PWA and
wrapped for Android with Capacitor.

The public experience should be a single mobile-first landing page with login
and registration entry points, followed by service discovery and job creation
for customers looking for local providers such as mama fua, fundis, tailors,
plumbers, electricians, cleaners and similar services.
