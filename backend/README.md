# Jijenge Backend — Phase 1

Production-oriented Go standard-library foundation for the Jijenge backend.

## Stack

- Go standard library
- `net/http`
- `log/slog`
- No ORM
- No external runtime dependencies in Phase 1

## Run

```bash
go test ./...
go run ./cmd/api
```

Then open:

- `GET /health`
- `GET /ready`

Default server:

```text
http://localhost:8080
```

## Configuration

Copy `.env.example` to your environment configuration. The Phase 1 app reads environment variables directly.

Important variables:

```text
APP_ENV
APP_HOST
APP_PORT
APP_READ_TIMEOUT
APP_WRITE_TIMEOUT
APP_IDLE_TIMEOUT
APP_SHUTDOWN_TIMEOUT
APP_MAX_BODY_BYTES
```

## Phase 1 security foundation

- Graceful shutdown
- Read/write/idle timeouts
- Header timeout
- Maximum request body size
- Panic recovery without leaking panic details
- Cryptographically random request IDs
- Structured logging
- Security response headers
- Centralized JSON responses
- Environment-driven configuration

## Phase 1 boundaries

No database, authentication, authorization, payments, or business modules are included yet. Those are deliberately introduced in later phases after this foundation is tested.


## Phase 2 — Security Foundation

Phase 2 adds:

- Secure password hashing using salted PBKDF2-HMAC-SHA256 with a high work factor, implemented with the standard library.
- Secure opaque token generation and SHA-256 token hashing for values that will later be persisted.
- Constant-time comparison helpers.
- Reusable validation primitives.
- Central application error definitions.
- In-memory rate limiting with bounded key storage.
- Explicit CORS allow-list; wildcard origins are rejected.
- Production configuration validation requiring a 32+ byte application secret.
- `Idempotency-Key` is permitted by the CORS policy for later payment and mutation endpoints.

### Important security boundary

Phase 2 provides cryptographic and middleware primitives. It does **not** implement login, JWT/session issuance, authorization/permissions, database access, payments, or the ledger yet. Those are implemented in later phases with dedicated tests and transaction boundaries.

For production password storage, the password hashing abstraction should be benchmarked and reviewed before launch. The project uses a standard-library PBKDF2 implementation here so the phase remains dependency-free and reproducibly testable offline; Argon2id can be introduced as a reviewed dependency when the production dependency policy permits it.


## Phase 4 — Authentication

Phase 4 adds the authentication domain:

- Registration
- Login
- Opaque access tokens
- Opaque refresh tokens
- Refresh-token hashing
- Refresh-token rotation
- Session revocation
- Logout
- Logout-all service operation
- Account status checks
- Generic invalid-credential responses
- Strict JSON decoding with unknown-field rejection
- Authentication DTOs, models, repositories, services, handlers and validators
- Authorization-header parsing primitives

### Token design

Jijenge does not put sensitive session state into a client-controlled JWT at this stage. Access tokens are opaque and refresh tokens are high-entropy random values. Persisted refresh tokens are stored only as SHA-256 hashes.

A later authentication phase can add the database-backed repositories, access-token persistence/introspection strategy, email verification, password reset and MFA/OTP workflows after the MySQL layer is wired into the application.

### Security boundary

The Phase 4 demo wiring uses in-memory repositories so the project remains executable without a MySQL driver. This is intentional: repository interfaces are defined first and can be replaced by transactional MySQL implementations without changing the service contract.


### Database-backed authentication

Phase 4 also includes raw-SQL MySQL repositories for users and sessions. They use the Phase 3 `database/sql` abstraction and no ORM.

Migration `003_session_access_token` adds a hashed access-token column so bearer access tokens can be validated server-side without storing plaintext tokens.

The global Phase 4 router keeps in-memory repositories for a dependency-free executable demo. Before production, `app.go` should construct the MySQL repositories from the Phase 3 database connection and inject them into the auth service. That wiring belongs in the application composition root, not inside handlers.


## Phase 5 — Authorization & Permissions

Phase 5 adds a reusable RBAC authorization layer:

- Roles
- Permissions
- User-to-role assignments
- Role-to-permission assignments
- Permission middleware
- Raw SQL MySQL authorization repository
- In-memory authorization repository for isolated tests
- Permission naming convention such as `tasks.read`, `tasks.approve`, `payments.verify`
- Authorization audit-log schema
- Deny-by-default middleware behavior
- Separation of authentication from authorization

### Security rule

Authentication answers **who are you?**

Authorization answers **what are you allowed to do?**

Handlers and services must not trust a role or permission supplied by the client. Permissions are resolved server-side from the authenticated user's database relationships.

The audit table is intentionally separate from the financial ledger that will be built later. Financial ledger entries will require stronger immutability, double-entry rules, idempotency and transactional controls.


## Phase 6 — Core Jijenge Domain

Phase 6 introduces the core task marketplace workflow without touching the financial ledger:

- Task categories
- Task creation
- Draft/published/in-progress/completed/cancelled lifecycle
- Applications
- One application per user per task
- Owner-only task state changes
- Application acceptance
- Worker assignment
- Worker submission
- Owner verification
- Explicit state-transition validation
- Task event/audit foundation
- Raw MySQL migration schema with foreign keys and indexes
- In-memory repository for deterministic unit tests

Money is represented only as integer minor units (`budget_cents` / `proposed_cents`). No floating point is used and Phase 6 does not move, reserve, release, or record money. That financial behavior belongs to the later ledger/payment phases.

Production assignment/acceptance must execute application acceptance and assignment creation in one MySQL transaction with row locks. The repository interfaces are intentionally structured so this transaction can be added without putting SQL into handlers.

## Phase 7 — Transactional Task Workflow

Phase 7 hardens task assignment for concurrent production traffic.

- Raw SQL MySQL task repository
- Atomic application acceptance + assignment creation
- MySQL transaction using `database/sql`
- `SELECT ... FOR UPDATE` locking
- Conditional status updates
- Database-level `UNIQUE(task_id)` guard against multiple assignments
- Task event written inside the same transaction
- Automatic rollback on any failure
- Concurrent acceptance test for the in-memory implementation

The financial boundary remains explicit: Phase 7 does not move or reserve money. Payment, escrow/hold, release, refunds, idempotency keys and the immutable ledger belong to the financial phases.


## Phase 8 — Financial Ledger Foundation

Phase 8 introduces the financial boundary. It does **not** connect to M-Pesa/PSP yet.

### Core rules

- Money is stored as integer minor units (`*_cents`), never floating point.
- Ledger transactions are double-entry: every transfer creates equal debit and credit entries.
- Ledger transaction and entry rows are immutable at the database level.
- Idempotency keys prevent retrying the same operation from moving money twice.
- Idempotency conflicts are rejected if the same key is reused for different request data.
- Account currency must match the transaction currency.
- Frozen/closed accounts cannot participate in transfers.
- Balance updates and ledger writes must occur in one MySQL transaction.
- Account rows are locked before balance mutation to prevent double spending.
- Holds separate `available` from `held` funds.
- Foreign keys use restrictive deletion for financial records.
- Financial records are not deleted as part of normal business operations.

### Important boundary

A PSP callback must never directly edit a balance. The future payment integration will translate verified provider events into an idempotent internal ledger operation. Provider references and webhook event IDs will be persisted separately, with signature verification and replay protection.

The ledger is the source of truth. Cached account balances are a performance projection that must be updated in the same database transaction as the corresponding ledger operation and periodically reconciled against ledger entries.

Phase 8 deliberately does not implement withdrawal, refunds, PSP settlement, fees, or task escrow business rules yet. Those operations require their own accounting rules and idempotency semantics.


## Phase 9 — Payment Provider Boundary

Phase 9 adds a secure provider boundary without hard-coding M-Pesa or any PSP into the financial ledger.

### Security

- Provider adapter abstraction
- HMAC-SHA256 webhook verifier
- Constant-time signature comparison
- 32+ byte provider secret requirement
- Provider event IDs
- Payload hashes
- Replay detection
- Provider reference uniqueness
- Amount and currency verification
- Payment state machine
- Database constraints for payment integrity

### Critical rule

A provider webhook is **not** trusted because it says `success`.

The flow is:

1. Verify the provider signature.
2. Parse only the normalized fields required by the application.
3. Record the provider event with a unique `(provider,event_id)`.
4. Reject an event if the same event ID has a different payload hash.
5. Locate the internal payment by provider reference.
6. Verify amount and currency match the original payment.
7. Apply a legal payment state transition.
8. Mark the webhook processed.

The provider adapter is deliberately separate from the ledger. A future provider integration will turn a verified, idempotent payment event into a ledger operation inside a financial transaction. It will never write balances directly.

### No real PSP credentials are included

Phase 9 provides the integration boundary and test provider verifier. Production credentials, callback URLs, provider-specific request signing, API calls, settlement and reconciliation are added only in the provider-specific integration phase after the provider is selected.


## Phase 10 — Atomic Payment Settlement

Phase 10 closes the critical payment-to-ledger boundary.

A verified successful provider event can now be handled through `ConfirmAndSettlePayment`. In the MySQL repository this is one InnoDB transaction that:

1. Locks the payment row.
2. Confirms the payment if it is pending.
3. Detects an already-settled payment.
4. Locks the provider clearing and destination balances in deterministic order.
5. Verifies account status and currency.
6. Verifies the provider clearing account has enough available funds.
7. Creates the immutable double-entry ledger transaction.
8. Debits the provider clearing balance.
9. Credits the user's balance.
10. Creates the payment settlement record.

Any failure rolls back the entire operation.

`payment_settlements` has unique constraints on payment, ledger transaction, and idempotency key.

### Provider clearing account

A provider clearing account must be configured and funded through a separate verified settlement/reconciliation process. The payment webhook itself does not create money out of thin air.

### Important

The memory repository is a deterministic unit-test double. The production atomic guarantee is implemented by the MySQL repository because payment rows, balances, ledger entries, and settlement records must share the same InnoDB transaction.


## Phase 11 — Task Escrow

Phase 11 adds task-level escrow.

- Owner funds escrow from an active financial account.
- Funding atomically moves `available` funds to `held` funds.
- Exactly one escrow can exist per assignment.
- Submission moves escrow to `submitted`.
- Verification/release atomically moves held funds from the owner's account to the worker's account and writes an immutable double-entry ledger transaction.
- Refund atomically returns held funds to the payer's available balance.
- Disputes freeze the escrow in a non-release state until an explicit resolution path is implemented.
- Account ownership, currency, status and amount are checked in the same transaction.
- Account rows are locked in deterministic order during release.
- Financial records are never deleted by escrow operations.

This phase intentionally does not auto-release money merely because a worker marks a task complete. The task owner/authorized verifier must explicitly verify the submission.


## Phase 12 — Disputes, Refunds & Platform Fees

Phase 12 adds controlled dispute resolution and platform fee accounting.

### Dispute flow

`submitted` → `disputed` → `resolved`

A dispute must be opened with a user and reason. Only an explicit resolution can finish it:

- `pay_worker`: release 100% to worker.
- `refund_payer`: return 100% to payer.
- `split_settlement`: release a defined worker amount and the remainder to the platform fee account.

All financial resolutions run inside the same MySQL transaction as balance updates and immutable ledger entries.

### Platform fees

A platform fee is represented as a real ledger credit to a dedicated platform financial account. It is never deducted by changing the worker's ledger entry after the fact.

Example:

KES 10,000 escrow with KES 1,000 fee:

- Payer debit: KES 10,000
- Worker credit: KES 9,000
- Platform credit: KES 1,000

The ledger remains balanced.

### Refunds

Refunding escrow returns held funds to the payer's available balance. Since the funds were reserved rather than transferred to another owner, this is a hold release, not a fabricated external payment.

### Security

- One open dispute per escrow.
- Disputes cannot be resolved twice.
- Worker amount cannot exceed escrow.
- Split settlement cannot pay zero or the full amount.
- Fee account is required for split settlement.
- Account locks are deterministic during financial settlement.
- Ledger idempotency keys are deterministic per escrow/dispute.
- Financial updates and escrow status changes are atomic.


## Phase 13 — Notifications & Messaging

Adds a notification domain with:

- In-app notifications with unread/read state.
- Per-user channel/event preferences.
- MySQL repository and testable memory repository.
- Notification outbox schema for reliable asynchronous email/SMS/push delivery.
- Idempotent outbox uniqueness per notification/channel.
- Bounded notification title/body validation.
- User-scoped reads so one user cannot mark another user's notification as read.
- Indexed unread/list queries.

The outbox is deliberately persisted separately from the notification record. A future worker can claim pending rows, deliver them through a provider, and retry failures without making the request path depend on an external messaging provider.

Financial and task operations should create notification records/outbox entries in the same business transaction where atomic delivery semantics are required; external delivery itself must remain asynchronous.


## Phase 14 — Audit, Reconciliation & Financial Monitoring

Adds a dedicated audit/reconciliation domain.

### Audit trail
`audit_events` records security-sensitive actions with actor, resource, request ID, IP, user agent, outcome, reason and optional JSON metadata. Audit records are append-only by application convention and are never used as a source of mutable financial truth.

### Reconciliation
`reconciliation_runs` and `reconciliation_issues` provide an operational record of integrity checks.

The first reconciliation check verifies every ledger transaction is balanced:

`SUM(debits) == SUM(credits)`

An unbalanced transaction becomes a recorded discrepancy instead of being silently ignored.

The reconciliation service also counts financial accounts and ledger transactions so an operator can see the scope of each run.

Future provider reconciliation can compare PSP-confirmed payments and settlement records against the ledger without changing historical ledger entries.

Financial ledger remains the source of truth; audit logs explain who/what/when, while reconciliation identifies inconsistencies.


## Phase 15 — Admin / Back-office Operational Controls

Adds controlled administrative actions with a two-person approval workflow.

Supported sensitive actions:
- block/unblock a user
- freeze/unfreeze a financial account

A request records the initiator, target, reason and status. The initiator cannot approve their own request. MySQL approval/execution runs in one transaction and records the resulting administrative action in the audit log in that same transaction.

No admin operation deletes ledger entries, payments, escrow records or historical financial data.


## Phase 16 — Security Hardening & Production Readiness

- Atomic refresh-token rotation.
- Maximum session lifetime (default 90 days) so refresh cannot extend a session forever.
- Rate limiting uses the direct peer address by default instead of trusting spoofable `X-Forwarded-For`.
- Production requires a strong secret and bounded HTTP timeouts.
- Security-event storage for sensitive application events.
- Session expiry and admin approval indexes.
- Reversible migration `015_security_hardening`.


## Phase 17 — Full Integration, E2E, Performance & Deployment Readiness

Adds an end-to-end critical-flow test covering authentication, refresh rotation, task lifecycle, application, assignment, submission, verification, ledger transfer/idempotency, escrow release, notifications, and two-person admin approval.

Adds invariant tests for insufficient funds and self-transfers, plus a rate-limiter benchmark. All 15 migration versions have matching reversible up/down files.

Deployment checklist:
- run migrations before starting the API;
- keep production secrets out of source control;
- terminate TLS at a trusted proxy/load balancer;
- configure trusted proxy/client-IP handling explicitly;
- configure CORS for known origins;
- run `go test ./...`, `go test -race ./...`, and `go build ./...` in CI;
- configure PSP webhook signing secrets and idempotent processing;
- run reconciliation and monitor audit/security events;
- maintain tested MySQL backups/restores;
- never expose database or migration endpoints publicly.


## Phase 18 — Marketplace, Matching, Location, Reputation & Settlement

Adds the marketplace layer without exposing internal accounting as public APIs.

### Marketplace
- Service categories and provider service listings.
- Provider profiles and service radius.
- Provider locations with validated coordinates.
- Existing tasks gain optional service and location fields.
- Location-aware nearby matching using Haversine distance.
- Ratings tied to completed assignments at the database level.
- One rating per assignment and no self-ratings.

### Settlement
A settlement is separate from a PSP payment.

Supported methods:
- platform
- cash
- mobile_money
- bank_transfer
- other

Offline settlement is explicitly represented as a claim/confirmation workflow. Jijenge does not claim to have processed cash. The payer claims payment and the payee confirms receipt; either party can dispute a claimed settlement.

### Architectural rule
Ledger, reconciliation, security and audit remain internal domain/infrastructure modules. They do not need ordinary public CRUD routes. Marketplace modules expose only the user-facing operations that actually belong in the API.


## Phase 19 — Docker & Local Deployment Infrastructure

Jijenge now has a multi-stage Docker build with separate `api` and `migrate` targets.

### Local setup

1. Copy `.env.example` to `.env`.
2. Replace the local passwords and `APP_SECRET_KEY`.
3. Start the stack:

```bash
docker compose up --build
```

The dependency order is:

```text
MySQL healthy
   ↓
migration container runs 001 → 016
   ↓
migration succeeds
   ↓
API starts
```

MySQL data is stored in the named `jijenge_mysql_data` volume.

Useful commands:

```bash
docker compose ps
docker compose logs -f api
docker compose logs migrate
docker compose run --rm migrate -command status
curl http://localhost:8080/health
docker compose down
```

`docker compose down` does not remove the database volume. To intentionally destroy local database data:

```bash
docker compose down -v
```

### Production

Do not use the example passwords. Use a secrets manager or deployment-platform secrets. Do not publish MySQL's port. Put TLS/reverse proxying in front of the API and configure trusted proxy handling explicitly.

The API image runs as the non-root `nonroot` user and contains only the statically compiled binary. The migration image is separate so migrations are not embedded into normal API startup.

The current API composition still uses in-memory repositories in `Routes.Register`; Docker does not magically switch those repositories to MySQL. Before a real production deployment, the application composition layer must inject the MySQL repositories into the API. Phase 19 deliberately keeps that existing architectural boundary intact rather than pretending the database is already wired into every handler.


## Phase 20 — Production MySQL Repository Wiring

The API now accepts a real `Database.DB` dependency. When `DB_DSN` is configured, the application opens MySQL once at startup and injects MySQL repositories into the HTTP composition for authentication and tasks:

```text
HTTP
 ↓
Services
 ↓
Repository interface
 ↓
MySQL repository
 ↓
Core Database
 ↓
MySQL / InnoDB
```

When `DB_DSN` is omitted in non-production environments, the existing in-memory repositories remain available for lightweight unit execution. Production validation requires `DB_DSN`.

`/ready` now checks the database connection when a DB is configured and returns `503` if the database is unavailable.

The API Docker target is built with the `mysql` build tag so the MySQL `database/sql` driver is registered only in the production/container binary.

### Important

Phase 20 wires the existing MySQL repositories that already implement the repository contracts. It does not claim that every Phase 18 marketplace repository is production-backed yet; those modules currently have memory repositories and need their own MySQL repository implementations before their public endpoints are enabled for production.


## Phase 21 — Production Financial & Marketplace Persistence

Phase 21 adds MySQL implementations for the remaining production persistence contracts:

- Financial ledger/accounts/balances
- Ledger holds
- Service categories/listings
- Provider profiles/locations
- Ratings
- Settlements

The financial repository uses InnoDB transactions and row locks for balance-changing operations. Ledger entries and transactions remain immutable at the database level through the existing triggers.

Marketplace modules keep the repository interfaces unchanged, so services do not know whether they are using memory or MySQL.

The provider `Nearby` query first applies a database bounding box and leaves the final distance ordering/filtering to the matching service.

### Production boundary

These repositories are production-ready at the repository-contract level, but a real MySQL integration environment should still be run before handling live money. The next hardening step is an automated Docker-based integration suite that exercises concurrent transfers, hold capture/release, settlement races, and migration upgrades against the same MySQL version used in deployment.


## Phase 22 — Real MySQL Integration & Concurrency Hardening

Phase 22 adds an executable MySQL integration suite and hardens the database layer for concurrent production use.

### Run the real MySQL suite

Docker is required:

```bash
cp .env.example .env
# Set strong local test passwords and APP_SECRET_KEY.
./scripts/run-mysql-integration.sh
```

The suite starts MySQL 8.4, waits for the health check, applies all migrations, then runs the tagged Go integration tests against that real MySQL instance.

The integration suite verifies:
- 16+ migrations are applied and clean;
- idempotent ledger retries return the same transaction;
- conflicting reuse of an idempotency key is rejected;
- opposite-direction concurrent transfers do not deadlock;
- concurrent reuse of one idempotency key creates exactly one ledger transaction;
- ledger balances remain correct;
- hold creation reserves available funds;
- conflicting hold references are rejected;
- hold release atomically restores the balance.

### Concurrency hardening

Financial transfers now lock both participating account rows in deterministic ascending ID order. This prevents the common A→B / B→A lock-order deadlock.

Migration `up` and `down` operations use a MySQL advisory lock (`GET_LOCK`) so two deployment processes cannot migrate the same database concurrently.

The suite uses a disposable Docker volume and removes it on completion.

The normal `go test ./...` suite remains database-independent. The tagged integration suite is the one that requires a real MySQL server.


### Validation performed in the build environment

The normal suite, build, and race detector pass. The real MySQL integration test is intentionally a tagged test because it requires the MySQL driver and a live MySQL server. The build environment used to create this artifact has no Docker daemon and cannot download uncached Go modules from the public network, so the tagged integration suite was not executed here. Run `./scripts/run-mysql-integration.sh` in GitHub Codespaces, your development machine, or CI to execute it against MySQL 8.4.


### Validation performed
- `go test ./...` — PASS
- `go build ./...` — PASS
- `go test -race ./...` — PASS


## Phase 24 — Payment / PSP Integration Hardening

Phase 24 adds the secure payment-provider boundary without hard-coding a particular PSP into the financial core.

### Payment flow

```text
PSP
 │
 │ signed webhook
 ▼
POST /api/v1/payments/webhook
 │
 ├─ bounded request body
 ├─ signature verification
 ├─ strict event validation
 ├─ webhook event idempotency
 ├─ payment amount/currency verification
 │
 ▼
MySQL transaction
 │
 ├─ confirm payment
 ├─ lock clearing + destination accounts
 ├─ create double-entry ledger transaction
 ├─ update balances
 └─ record payment settlement
```

### Provider abstraction

`Payments/Provider` now remains the boundary between a PSP and Jijenge. The included HMAC-SHA256 verifier is suitable for providers that authenticate callbacks this way; a real PSP adapter should implement the same `Verifier` contract using that PSP's documented signature scheme.

The application does not trust arbitrary PSP JSON. It verifies the signature first, then maps the provider event into the small internal `IncomingEvent` contract.

### Replay and idempotency

Webhook event IDs are unique per provider. Repeated delivery of the same signed event is safe.

A confirmed payment cannot be settled again with a different provider event.

The settlement path also protects the ledger from applying an existing idempotency-key transaction's balance mutation a second time.

### Enabling the webhook

Set:

```text
PAYMENT_PROVIDER_NAME=your-provider
PAYMENT_WEBHOOK_SECRET=<32+ byte secret>
PAYMENT_CLEARING_ACCOUNT_ID=<financial clearing account ID>
```

The webhook route is only registered when a provider is explicitly configured. Production configuration rejects a payment configuration with a weak webhook secret or missing clearing account.

The endpoint is:

```text
POST /api/v1/payments/webhook
X-Provider-Signature: <provider signature>
```

Do not use the generic HMAC verifier for a PSP unless that PSP's official webhook documentation specifies HMAC-SHA256 over the exact raw request body. For M-Pesa/Daraja or another provider with a different callback/authentication model, implement that provider's adapter instead of weakening the generic verifier.

### Validation

- `go test ./...` — PASS
- `go build ./...` — PASS
- `go test -race ./...` — PASS

A live PSP sandbox was not contacted because credentials/provider selection have not been supplied. The code is structured so the actual provider adapter can be plugged in without changing the ledger.


## Phase 25 — Marketplace Workflow API

Phase 25 completes the authenticated task workflow API:

```text
Task draft
  ↓
Published
  ↓
Applications
  ↓
Owner accepts application
  ↓
Assignment created atomically
  ↓
Worker submits
  ↓
Owner verifies
  ↓
Rating between the actual task owner and worker
```

### New workflow endpoints

```text
POST /api/v1/tasks/{id}/start
POST /api/v1/tasks/{id}/complete
POST /api/v1/tasks/{id}/cancel

POST /api/v1/applications/{id}/accept

POST /api/v1/assignments/{id}/submit
POST /api/v1/assignments/{id}/verify

POST /api/v1/assignments/{id}/ratings
GET  /api/v1/users/{id}/rating
```

All state-changing workflow endpoints require authentication.

The existing service/repository ownership checks remain authoritative. In particular:

- only the task owner can publish/start/complete/cancel;
- only the task owner can accept an application;
- a task can only receive one assignment;
- only the assigned worker can submit;
- only the task owner can verify;
- ratings are only accepted for a verified assignment;
- a rating must be between the actual owner/worker pair;
- duplicate ratings are rejected.

The MySQL rating repository now validates the assignment relationship and verified state in the database before inserting the rating, rather than trusting the HTTP request's `reviewee_user_id`.

### Deliberate boundary

Phase 25 does not automatically release escrow merely because an HTTP verification endpoint succeeds. Financial release remains in the escrow/payment transaction boundary. This prevents a marketplace workflow endpoint from accidentally creating a money movement outside the financial controls already established in Phases 22–24.

### Validation

- `go test ./...` — PASS
- `go build ./...` — PASS
- `go test -race ./...` — PASS


## Phase 26 — Escrow Lifecycle & Verified Release

Phase 26 connects the marketplace workflow to the financial escrow boundary.

### Flow

```text
Application accepted
      ↓
Owner funds escrow
      ↓
Worker performs task
      ↓
Worker submits
      ↓
Escrow → submitted
      ↓
Owner verifies
      ↓
Escrow → released
      ↓
Ledger:
payer held balance decreases
worker available balance increases
```

### New endpoints

```text
POST /api/v1/escrows
POST /api/v1/escrows/{id}/dispute
POST /api/v1/assignments/{id}/release
```

The release endpoint is a safe retry mechanism when verification succeeds but a financial release temporarily fails.

### Security

Funding is bound to the authenticated task owner and the MySQL transaction independently verifies the requester, task/assignment relationship, task amount/currency, payer ownership, worker ownership, account status, currency, and payer balance.

Disputes are restricted at the MySQL boundary to the payer or assigned worker.

Verified release is authorized at the database boundary: only the task owner can release a verified assignment.

### Atomic settlement

Verified release runs inside one MySQL transaction that locks the verified assignment, escrow and financial balances, moves the payer's held balance, creates the idempotent ledger transaction, credits the worker, and marks escrow released. Any failure rolls back the transaction.

### Validation

- `go test ./...` — PASS
- `go build ./...` — PASS
- `go test -race ./...` — PASS


# Phase 27 — Manual/Cash Settlement Integrity

Phase 27 adds a controlled settlement workflow for payments that happen outside Jijenge, especially cash.

## Why this exists

Jijenge must not pretend that cash was paid simply because an owner clicked a button.

For an external/manual payment:

```text
Owner says payment was made
        ↓
Settlement recorded as PENDING
        ↓
Worker/payee claims receipt
        ↓
Worker confirms receipt
        ↓
Settlement becomes CONFIRMED
```

The platform records the event and evidence, but **cash never enters the Jijenge financial ledger**.

Platform escrow remains separate:

```text
Platform payment
    ↓
Escrow
    ↓
Ledger
    ↓
Worker balance
```

Manual/cash payment:

```text
Cash / external payment
    ↓
Settlement record
    ↓
Two-party confirmation
    ↓
Audit/reconciliation visibility
```

## New endpoints

```text
POST /api/v1/settlements

POST /api/v1/settlements/{id}/claim

POST /api/v1/settlements/{id}/confirm

POST /api/v1/settlements/{id}/dispute
```

## Security controls

Manual settlement creation:

- requires authentication;
- only the task owner can create it;
- `platform` settlement creation is rejected from the public manual endpoint;
- payer and payee cannot be the same user;
- assignment must belong to the supplied task;
- payee must be the actual assigned worker;
- task amount and currency must match;
- the assignment must have reached `submitted` or `verified`;
- an existing escrow for the assignment blocks manual settlement creation;
- an evidence reference is required.

This prevents a user from creating a fake cash settlement against another user's task or using the cash workflow to bypass an active platform escrow.

## Confirmation

The payer cannot directly mark a cash settlement as confirmed.

```text
Payer → Claim
Payee → Confirm
```

Confirmation stores a confirmation note.

Disputes require a reason and can be opened by either party while the settlement is claimed.

## Database migration

Phase 27 adds migration:

```text
017_settlement_integrity.up.sql
017_settlement_integrity.down.sql
```

New fields:

- `evidence_reference`
- `confirmation_note`
- `dispute_reason`

It also adds an assignment/status index and a database check requiring evidence once a settlement leaves `pending`.

## Testing

```text
go test ./...        PASS
go build ./...       PASS
go test -race ./...  PASS
```


# Phase 28 — Financial Mutation Idempotency & Replay Protection

Phase 28 hardens the two most important external financial mutation paths:

- platform escrow funding;
- manual/external settlement creation.

## Why this matters

Mobile networks, browsers, reverse proxies and clients can retry a request after a timeout even when the server already completed it.

Without idempotency:

```text
Client
  │
  ├── fund request ──────→ server
  │                         │
  │                         └── money held
  │
  └── retry ─────────────→ server
                            │
                            └── possible second operation
```

Phase 28 changes this to:

```text
Client + Idempotency-Key
          ↓
First request → execute once
          ↓
Retry with same key + same payload
          ↓
Return the original resource
```

A reused key with a different financial payload is rejected.

## Header

Financial creation requests now require:

```http
Idempotency-Key: <16-to-128-character-key>
```

Examples:

```http
POST /api/v1/escrows
Idempotency-Key: escrow-01J...
```

```http
POST /api/v1/settlements
Idempotency-Key: settlement-01J...
```

The client should generate a new unpredictable key for every new financial operation and reuse that key only when retrying the exact same operation.

## Escrow protection

`POST /api/v1/escrows` now uses the authenticated owner path:

```text
HTTP authentication
      ↓
FundForUser()
      ↓
database verifies task ownership
      ↓
idempotency check
      ↓
balance lock
      ↓
hold funds
      ↓
create escrow
```

This also closes an important architectural gap from the earlier implementation: the public handler no longer uses the unrestricted `Fund()` path.

## Manual settlement protection

Manual cash/external settlement creation also requires an idempotency key.

The database verifies the key against the payer and rejects a changed request using the same key.

This prevents:

- duplicate cash settlement records from client retries;
- duplicate external-payment records;
- accidental reuse of a key for a different amount;
- accidental reuse for a different worker;
- accidental reuse for a different task/assignment.

## Database

Migration:

```text
018_idempotency.up.sql
018_idempotency.down.sql
```

It adds unique idempotency keys scoped to the financial actor:

```text
escrow:
(payer_account_id, idempotency_key)

settlement:
(payer_user_id, idempotency_key)
```

Existing records are safely backfilled with deterministic legacy keys before the columns become `NOT NULL`.

## Retry semantics

Same key + same request:

```text
200/201-style successful resource response
```

Same key + different request:

```text
rejected
```

Different key + new request:

```text
new operation
```

The unique constraint is enforced by MySQL, not only by Go code, so concurrent requests cannot bypass the protection.

## Tests

Verified:

```text
go test ./...                              PASS
go build ./...                            PASS
go test -race ./Escrow/... ./Settlements/... ./Routes/... PASS
```

The complete repository race run was also attempted; the execution environment interrupted it due to its runtime limit, while the race tests covering the Phase 28 financial modules and routing completed successfully.


# Phase 29 — Tamper-Evident Audit Trail

Phase 29 hardens Jijenge's audit system.

Financial operations, permissions, security actions and administrative events should leave evidence that can be checked later. A normal audit table records history, but a privileged database user who changes an old row could otherwise alter the history silently.

Phase 29 adds a SHA-256 hash chain to new audit events.

## Chain

```text
Event 1
previous_hash = NULL
event_hash = SHA256(event data)

        ↓

Event 2
previous_hash = Event 1.event_hash
event_hash = SHA256(previous_hash + Event 2 data)

        ↓

Event 3
previous_hash = Event 2.event_hash
event_hash = SHA256(previous_hash + Event 3 data)
```

Changing Event 1 changes its hash and breaks Event 2's link.

Changing Event 2 changes its hash and breaks Event 3's link.

## Database

Migration:

```text
019_audit_integrity.up.sql
019_audit_integrity.down.sql
```

New columns:

```text
previous_hash CHAR(64)
event_hash    CHAR(64)
```

Existing historical audit rows are left unhashed rather than being given fake hashes. The integrity chain begins with the first audit event written after Phase 29 is deployed. This is intentional: it does not pretend that old records have cryptographic provenance that they did not previously have.

## Transactional recording

MySQL audit writes now run in a serializable transaction.

The repository:

1. obtains the latest hashed audit event;
2. locks it;
3. calculates the new event hash;
4. inserts the event and both hashes in the same transaction.

This prevents concurrent writers from silently creating two competing chain positions.

## Verification

The audit repository and service now expose:

```go
VerifyChain(ctx)
```

Verification recalculates every hashed event and checks:

```text
previous_hash == previous event_hash
event_hash == SHA256(canonical event data)
```

A failure returns:

```text
audit chain integrity failure
```

## Important security boundary

This is **tamper-evident**, not magical tamper-proof storage.

If an attacker obtains unrestricted database access, they may be able to rewrite both records and hashes. Production deployment should therefore also protect the database with:

- least-privilege DB credentials;
- restricted network access;
- encrypted backups;
- backup immutability/WORM where appropriate;
- separate operational and audit permissions;
- monitoring/alerting around audit verification failures.

The hash chain gives Jijenge a strong mechanism to detect unauthorized modification; it does not replace database security.

## Testing

```text
go test ./...                  PASS
go build ./...                PASS
go test -race ./Audit/...     PASS
```

Tests cover:

- SHA-256 hash generation;
- event-to-event chaining;
- successful chain verification;
- detection of tampering with an earlier audit event.


# Phase 30 — Reliable Notification Outbox & Delivery Worker

Phase 30 turns Jijenge's existing `notification_outbox` table into a real transactional outbox.

This is important because notifications can be triggered by financial and marketplace state changes. The application must not lose a notification merely because an email/SMS/push provider is temporarily unavailable.

## Before

A notification was written directly to the notification table.

That is fine for in-app notifications, but external delivery needs a reliable hand-off.

## Now

```text
Business operation
      ↓
DB transaction
      ├── notification row
      └── outbox row
              ↓
        dispatcher claims work
              ↓
        Email / SMS / Push provider
              ↓
          success?
         /       \
       yes        no
       ↓           ↓
     SENT       FAILED
                   ↓
                backoff
                   ↓
                 retry
```

The notification and outbox record are created in the same MySQL transaction. If the transaction rolls back, neither is created.

## Outbox channels

External delivery is queued for:

```text
email
sms
push
```

`in_app` notifications remain directly available from the notifications table and do not require an external provider.

## Safe claiming

The MySQL repository uses:

```sql
FOR UPDATE SKIP LOCKED
```

so multiple dispatcher workers can operate concurrently without claiming the same outbox row.

A worker that dies while processing an item does not permanently strand it. Processing rows older than ten minutes are returned to `pending`.

## Retry behavior

Failed delivery becomes:

```text
failed
```

and `available_at` is moved forward using exponential backoff with a five-minute maximum.

This avoids hammering an unavailable provider.

## At-least-once delivery

The dispatcher intentionally provides **at-least-once** processing.

A provider can therefore potentially receive the same message more than once in an unusual crash window:

```text
provider accepts message
        ↓
worker crashes before marking SENT
        ↓
outbox retries
```

Providers that support idempotency should use the outbox `PublicID` as their provider idempotency key.

This is preferable to silently losing a notification.

## New reusable components

```text
Notifications/Models/outbox.go

Notifications/Services/outbox_service.go
Notifications/Services/outbox_service_test.go
```

The delivery provider is deliberately an interface:

```go
type Delivery interface {
    Deliver(context.Context, Models.Outbox) error
}
```

That allows separate adapters for:

- M-Pesa/SMS-related notification providers;
- email providers;
- push notification providers;
- development/test providers.

The core Jijenge notification system does not become coupled to a specific vendor.

## No migration required

The `notification_outbox` table already existed from the earlier notification architecture. Phase 30 completes the application/repository/worker implementation around that table.

## Security and reliability

The dispatcher:

- uses bounded batch sizes;
- respects request cancellation;
- does not expose provider errors to API clients;
- stores a bounded error message;
- retries failed delivery;
- recovers stale processing locks;
- supports concurrent workers;
- keeps external delivery outside the request transaction;
- preserves the notification/outbox atomicity boundary.

## Testing

```text
go test ./...                         PASS
go build ./...                       PASS
go test -race ./Notifications/...   PASS
```

# Phase 31 — External Review Fixes: Migration, Provisioning, RBAC, API Ergonomics

Phase 31 addresses four issues found during an external, hands-on review that
went beyond reading the code: the reviewer installed a real MySQL 8.0
instance, ran `cmd/migrate` against it from a clean database, started the API
with the database wired in, and pushed real money through the full escrow
lifecycle over HTTP. That process is the only reason these were caught --
none of them were visible from `go test ./...` alone, because the existing
test suite uses in-memory repositories and never exercises `cmd/migrate` or a
live database at all.

## 1. `cmd/migrate` could not stand up a fresh database

`migrations/007_financial_ledger.up.sql` (and its duplicate under
`cmd/migrate/migrations/`) used `DELIMITER //` to define the ledger
immutability triggers. `DELIMITER` is a `mysql`-CLI-only meta-command; it is
not real SQL and is not understood by `database/sql` or any programmatic
MySQL driver, including the one `cmd/migrate` itself uses. Running
`cmd/migrate -command up` against a fresh database failed with a syntax
error on migration 7. Because DDL is not transactional in MySQL, the tables
from that migration were left partially created while the migration was
recorded as **dirty**, permanently blocking `cmd/migrate -command up` from
making further progress without manual database surgery.

Investigating this further surfaced a second, more fundamental problem: the
default `docker-compose.yml` DSN did not set `multiStatements=true` at all,
so migration 1 (which contains multiple `CREATE TABLE` statements in one
file) failed immediately -- before migration 7 was ever reached. The
documented deployment path (`docker compose up --build`, which runs the
`migrate` service before `api`) could not complete on a brand-new database.

**Fix:**
- Removed the `DELIMITER //` / `DELIMITER ;` directives from both copies of
  `007_financial_ledger.up.sql`. The trigger bodies are unchanged; they are
  now plain `CREATE TRIGGER ... BEGIN ... END;` statements with ordinary
  semicolons. This was verified empirically, not just assumed: sending
  multi-statement SQL (including `BEGIN...END` trigger bodies) over the wire
  with `multiStatements=true` works correctly without any client-side
  delimiter switching -- `DELIMITER` is purely an interactive `mysql`-CLI
  convenience and has no equivalent requirement at the protocol level.
- Added `multiStatements=true` to the `migrate` service's `DB_DSN` in
  `docker-compose.yml`. The `api` service's `DB_DSN` deliberately does
  **not** get this flag -- the running application never needs to send
  stacked statements, and there is no reason to widen its attack surface for
  a capability only the one-shot migration tool needs.

**Validation performed:** dropped and recreated a MySQL 8.0 database,
ran `cmd/migrate -command up` with the exact DSN shape from the fixed
`docker-compose.yml`, and confirmed all 19 migrations applied with
`dirty = 0` and all four ledger-immutability triggers present, on the first
attempt, no manual intervention. Also confirmed the triggers still correctly
reject `UPDATE`/`DELETE` on `ledger_entries` and `ledger_transactions` after
this change.

**Operational note for production MySQL:** creating a trigger requires
either the `SUPER` privilege or `log_bin_trust_function_creators = 1` when
binary logging is enabled, because MySQL cannot otherwise guarantee a
trigger body is replication-safe. Standalone/dev MySQL (including the
`mysql:8.4` image used by `docker-compose.yml`, which does not enable
binary logging by default) is unaffected. Managed MySQL (RDS, Cloud SQL,
etc.) with binary logging on for replication/backups may require this to be
set explicitly for the migration user -- check your provider's parameter
group / flag documentation before running migrations there for the first
time.

## 2. No way to provision a financial account through the API

`POST /api/v1/escrows` requires `PayerAccountID` / `WorkerAccountID`, but
nothing reachable over HTTP ever created a `financial_accounts` row.
`Financial.Services.CreateAccount` existed only at the service/repository
layer. A brand-new registered user had no wallet and no way to get one
without an operator inserting rows directly into the database -- which is
what the reviewer had to do to test the escrow flow at all in the prior
review pass.

**Fix:** `AuthHandler` now accepts an optional `AccountProvisioner` hook,
wired at composition time in `Routes.Register` (Auth still does not import
Financial directly, matching the existing pattern of composing cross-domain
side effects at the routing layer rather than inside a service). When a
database is configured, every successful registration now provisions a
zero-balance ledger account in the platform's default currency
(`APP_DEFAULT_CURRENCY`, defaults to `KES`), and the new account's ID is
returned in the registration response as `financial_account_id`.

Provisioning is deliberately best-effort: if it fails, registration still
succeeds (the user's login credentials are valid either way) and the
failure is logged server-side for an operator to provision the account
manually. This is safe specifically because a new account always starts at
a zero balance -- a missing account can only block that user from
funding/receiving escrow until it exists; it can never produce an
inconsistent financial state.

**Validation performed:** registered a new user against a live MySQL
database and confirmed the response included `financial_account_id`, then
confirmed the corresponding `financial_accounts` and `financial_balances`
rows existed with the correct owner, currency, and zero balance.

## 3. Authorization (RBAC) management endpoints were dead code

`Authorization/routes.go` defined a `RegisterRoutes` function that nothing
in the application ever called. `/api/v1/authorization/roles` and
`/api/v1/authorization/permissions` did not exist at runtime, despite the
handler, service, and MySQL repository all being fully implemented and
tested in isolation.

**Fix:** both routes are now registered in `Routes.Register`, gated behind
authentication **and** the existing `authorization.manage` permission
(enforced via `Authorization/Middleware.PermissionMiddleware`, which was
also previously unused). They were not simply exposed as open endpoints --
role/permission creation is a privilege-escalation-sensitive operation, so
an unauthenticated or unprivileged caller is rejected.

**Bootstrap note:** a fresh database has no roles, permissions, or grants at
all, so nobody can satisfy `authorization.manage` on day one. An operator
must seed the first permission, role, and grant directly via SQL (or a
trusted internal script) before these endpoints can be used to manage
authorization going forward -- the same kind of one-time seed step already
required for `task_categories` before tasks can be created.

**Validation performed:** confirmed live that an unauthenticated request to
`POST /api/v1/authorization/roles` returns `401`, and an authenticated
request from a user with no `authorization.manage` grant returns `403` --
i.e. the routes are reachable but correctly locked down, not an open
escalation path.

## 4. Workflow endpoints returned empty `204` bodies

`publish`, `start`, `complete`, `cancel`, `submit`, and `verify` all
returned `204 No Content` on success, forcing every client to make a
follow-up `GET` just to learn whether the action actually changed the
resource's state.

**Fix:** these six endpoints now return `200 OK` with a minimal JSON body,
e.g. `{"status": "published"}` / `{"status": "verified"}`, using the same
status vocabulary already defined in `Tasks/Models`. This is a pure
response-shape change -- no service, repository, or database behavior was
touched, and the underlying `writeStateError` / `writeAssignmentError`
error paths are unchanged.

**Validation performed:** re-ran the full task -> publish -> apply -> accept
-> fund escrow -> submit -> verify flow against a live MySQL database after
this change and confirmed both the new response bodies (`{"status":
"published"}`, `{"status": "submitted"}`, `{"status": "verified"}`) and the
underlying ledger correctness (balanced double-entry transaction, correct
final balances) were unaffected.

## Also fixed in this pass

- `go vet ./...` previously flagged an unused `fmt.Sprint` result in
  `Financial/Repositories/mysql_ledger_repository.go` -- this was dead
  placeholder code (`func (r *MySQLRepository) _unused() { fmt.Sprint("") }`)
  that existed only to keep the `fmt` import alive. Removed the function and
  the now-unused import. `go vet ./...` is now completely clean.

## What Phase 31 deliberately did not change

- The remaining unwired domains from the prior review (Financial read
  endpoints beyond what payments/escrow already use internally, Admin
  two-person approval, Providers/Services marketplace CRUD, Matching) are
  still not exposed as public HTTP routes. They were out of scope for this
  pass, which focused on making the existing, already-wired money-movement
  path actually deployable and usable end-to-end.
- No production secrets, connection strings, or credentials were added or
  changed. `.env.example` still requires an operator to supply real values.

## Validation

```text
go build ./...        PASS
go vet ./...           PASS (previously 1 warning)
go test ./...          PASS
go test -race ./...    PASS
```

Additionally, unlike every prior phase's validation section in this README,
this phase's fixes were verified against a real, freshly created MySQL 8.0
database using the same DSN shape as `docker-compose.yml`, including a live
HTTP trace of registration, login, task creation, publish, application,
acceptance, escrow funding, submission, verification, and escrow release --
confirming both the API-level fixes and the underlying financial
correctness (balanced ledger, correct final balances, working immutability
triggers) together, not separately.
