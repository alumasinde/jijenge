# Jijenge Migration Fix

Files included:
- `backend/migrate.py`
- `backend/migrations/066_create_assignment_lifecycle.sql`

## What changed

1. Already-applied migrations whose checksum changed are now warned about and skipped by default instead of stopping the migration run.
2. Strict checksum behavior remains available with:
   `MIGRATION_STRICT_CHECKSUMS=1`
3. Migration 066 is made safe for the current partially-applied database:
   - existing assignment status rows are reused/updated;
   - the lifecycle columns are added using standard MySQL `ALTER TABLE ... ADD COLUMN` syntax;
   - the old provider index from migration 025 is replaced with the lifecycle-aware definition;
   - the lifecycle status index and foreign key are completed.
4. MySQL 8.4 is used by the project's Docker Compose configuration.

## Run

From `/workspaces/jijenge`:

    docker compose run --rm migrate

Do not drop the database first.

If you want the old fail-fast checksum behavior:

    MIGRATION_STRICT_CHECKSUMS=1 docker compose run --rm migrate

## Important correction

The first fix package used `ADD COLUMN IF NOT EXISTS`. Your MySQL environment rejects that syntax, as shown by error 1064. The replacement package removes that syntax.

The screenshot shows the failure happened while parsing the first `ALTER TABLE`, so the lifecycle columns were not added. The earlier `CREATE TABLE assignment_statuses` and status inserts may already have succeeded; this migration therefore keeps `CREATE TABLE IF NOT EXISTS` and uses `ON DUPLICATE KEY UPDATE` for those rows.
