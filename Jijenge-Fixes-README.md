# Jijenge Test/CI Fixes

This package contains the files needed to apply the current testability and CI fixes
to the `alumasinde/jijenge` repository.

## Files

- `backend/migrate.py`
  - Loads `app.config.settings` lazily inside `get_connection()`.
  - Migration parser tests can therefore run without MySQL configuration.
  - Preserves migration checksum, ordering, parsing, and transaction logic.

- `backend/app/Modules/Financials/Services/commission_service.py`
  - Loads `db_connection` lazily inside `finalize_job_financials()`.
  - Pure commission calculation tests no longer require MySQL configuration.

- `backend/tests/conftest.py`
  - Supplies safe test-only environment variables before test collection.
  - Does not start MySQL and does not make production settings optional.
  - Database integration tests remain opt-in through `RUN_DB_TESTS=1`.

- `.github/workflows/ci.yml`
  - Runs pytest, the security audit, and migration validation on pushes/PRs.
  - Provides a MySQL service for future/integration database tests.

## Apply

Extract this ZIP over your existing repository, preserving the paths.

Then in Codespaces:

```bash
cd /workspaces/jijenge/backend

python -m pytest tests/test_migration_parser.py -v
python -m pytest tests/test_phase16_commission.py -v
python -m pytest tests/test_security_basics.py -v
python -m pytest -v
```

This ZIP is an overlay of the fixes, not a replacement copy of the entire Git
repository. Your existing application source and migrations are intentionally
left untouched except for the two corrected source files above.
