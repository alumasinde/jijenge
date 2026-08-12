from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

import mysql.connector


MIGRATION_PATTERN = re.compile(r"^(\d+)_([A-Za-z0-9_-]+)\.sql$")


def checksum_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_connection():
    """
    Create a MySQL connection.

    Configuration is imported lazily here instead of at module import time.
    This allows database-independent functions such as split_sql_statements()
    to be imported and tested without requiring MySQL environment variables.
    """
    from app.config import settings

    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=settings.mysql_database,
        user=settings.mysql_user,
        password=settings.mysql_password,
        autocommit=False,
    )


def migration_table_exists(connection) -> bool:
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = 'schema_migrations'
            """
        )
        return bool(cursor.fetchone()[0])
    finally:
        cursor.close()


def load_applied(connection) -> dict[str, dict]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT version, filename, checksum
            FROM schema_migrations
            ORDER BY version
            """
        )
        rows = cursor.fetchall()
        return {row["version"]: row for row in rows}
    finally:
        cursor.close()


def load_migrations() -> list[tuple[str, Path]]:
    migration_dir = Path(__file__).resolve().parent / "migrations"
    migrations = []

    for path in migration_dir.glob("*.sql"):
        match = MIGRATION_PATTERN.match(path.name)

        if not match:
            raise RuntimeError(
                f"Invalid migration filename: {path.name}. "
                "Expected format like 001_create_users.sql"
            )

        version = match.group(1)
        migrations.append((version, path))

    migrations.sort(key=lambda item: int(item[0]))

    seen_versions = set()

    for version, path in migrations:
        if version in seen_versions:
            raise RuntimeError(f"Duplicate migration version: {version}")
        seen_versions.add(version)

    return migrations


def split_sql_statements(sql: str) -> list[str]:
    """
    Split ordinary MySQL migration SQL on semicolons while respecting:

    - single quoted strings
    - double quoted strings
    - backtick identifiers
    - escaped characters
    - MySQL single-line comments
    - MySQL block comments

    Migration files in this project deliberately avoid stored procedures,
    triggers, custom DELIMITER blocks, and other constructs that require a
    full SQL parser.
    """
    statements: list[str] = []
    current: list[str] = []

    in_single = False
    in_double = False
    in_backtick = False
    escape = False
    i = 0

    while i < len(sql):
        char = sql[i]
        next_char = sql[i + 1] if i + 1 < len(sql) else ""

        if escape:
            current.append(char)
            escape = False
            i += 1
            continue

        if char == "\\" and (in_single or in_double):
            current.append(char)
            escape = True
            i += 1
            continue

        if char == "'" and not in_double and not in_backtick:
            in_single = not in_single
            current.append(char)
            i += 1
            continue

        if char == '"' and not in_single and not in_backtick:
            in_double = not in_double
            current.append(char)
            i += 1
            continue

        if char == "`" and not in_single and not in_double:
            in_backtick = not in_backtick
            current.append(char)
            i += 1
            continue

        if not in_single and not in_double and not in_backtick:
            if char == "#" or (char == "-" and next_char == "-"):
                while i < len(sql) and sql[i] != "\n":
                    i += 1
                current.append("\n")
                continue

            if char == "/" and next_char == "*":
                end = sql.find("*/", i + 2)
                if end == -1:
                    raise RuntimeError("Unclosed SQL block comment")
                i = end + 2
                current.append(" ")
                continue

        if char == ";" and not in_single and not in_double and not in_backtick:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)

        i += 1

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)

    return statements


def apply_migration(
    connection,
    version: str,
    path: Path,
    checksum: str,
) -> None:
    sql = path.read_text(encoding="utf-8").strip()

    if not sql:
        raise RuntimeError(f"Migration is empty: {path.name}")

    statements = split_sql_statements(sql)
    if not statements:
        raise RuntimeError(
            f"Migration contains no executable SQL: {path.name}"
        )

    cursor = connection.cursor()

    try:
        print(f"  Running {path.name} ...")

        for statement in statements:
            cursor.execute(statement)

        cursor.execute(
            """
            INSERT INTO schema_migrations
                (version, filename, checksum)
            VALUES
                (%s, %s, %s)
            """,
            (version, path.name, checksum),
        )

        connection.commit()
        print(f"  ✓ {path.name}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()


def run(check_only: bool = False) -> None:
    print("Database Migration Manager")
    print("=" * 28)

    connection = None

    # Set MIGRATION_STRICT_CHECKSUMS=1 if you want the old fail-fast
    # behavior when an already-applied migration file was edited.
    strict_checksums = os.getenv("MIGRATION_STRICT_CHECKSUMS", "").lower() in {
        "1", "true", "yes", "on"
    }

    try:
        connection = get_connection()
        print("Connected to MySQL ✓")

        migrations = load_migrations()

        # Migration 001 owns creation of schema_migrations.
        if migration_table_exists(connection):
            applied = load_applied(connection)
        else:
            applied = {}

            if not migrations or migrations[0][0] != "001":
                raise RuntimeError(
                    "schema_migrations is missing and migration 001 "
                    "is not the first migration"
                )

        for version, path in migrations:
            checksum = checksum_file(path)

            if version in applied:
                previous = applied[version]

                if previous["filename"] != path.name:
                    raise RuntimeError(
                        f"Migration {version} filename changed: "
                        f"{previous['filename']} -> {path.name}"
                    )

                if previous["checksum"] != checksum:
                    message = (
                        f"Migration {version} was already applied, but its "
                        "current file checksum differs from the recorded "
                        "checksum. Skipping because the migration is already "
                        "recorded as applied."
                    )

                    if strict_checksums:
                        raise RuntimeError(
                            message
                            + " MIGRATION_STRICT_CHECKSUMS is enabled."
                        )

                    print(f"  ⚠ {message}")

        pending = [
            (version, path, checksum)
            for version, path in migrations
            if version not in applied
        ]

        if not pending:
            print("Database is already up to date ✓")
            return

        print(f"Pending migrations: {len(pending)}")

        for version, path, checksum in pending:
            print(f"  Pending: {path.name}")

            sql = path.read_text(encoding="utf-8").strip()

            if not sql or not split_sql_statements(sql):
                raise RuntimeError(
                    f"Migration contains no executable SQL: {path.name}"
                )

        if check_only:
            print("Migration check completed successfully ✓")
            return

        for version, path, checksum in pending:
            apply_migration(connection, version, path, checksum)

        print("Migration completed successfully ✓")

    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    run(check_only="--check" in sys.argv)
