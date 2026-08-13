#!/usr/bin/env python3
"""Static validation for Jijenge MySQL migrations."""
from __future__ import annotations

import re
from pathlib import Path

PATTERN = re.compile(r"^(\d+)_([A-Za-z0-9_-]+)\.sql$")
CREATE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([A-Za-z0-9_]+)`?", re.I)
REFERENCES = re.compile(r"REFERENCES\s+`?([A-Za-z0-9_]+)`?\s*\(", re.I)
UNSUPPORTED_MYSQL = re.compile(
    r"\bALTER\s+TABLE\b.*?\bADD\s+(?:COLUMN|CONSTRAINT)\s+IF\s+NOT\s+EXISTS\b",
    re.I | re.S,
)


def strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    sql = re.sub(r"(?m)^\s*--.*$", "", sql)
    sql = re.sub(r"(?m)^\s*#.*$", "", sql)
    return sql


def validate(directory: Path) -> tuple[int, int]:
    files = [p for p in directory.glob("*.sql") if PATTERN.match(p.name)]
    files.sort(key=lambda p: int(PATTERN.match(p.name).group(1)))

    if not files:
        raise RuntimeError("No migrations found")

    seen_versions: set[str] = set()
    tables: set[str] = set()
    created_by: dict[str, str] = {}
    errors: list[str] = []
    expected_version = 1

    for path in files:
        match = PATTERN.match(path.name)
        assert match is not None
        version = match.group(1)
        version_number = int(version)

        if version in seen_versions:
            errors.append(f"duplicate migration version: {version}")
        seen_versions.add(version)

        if version_number != expected_version:
            errors.append(
                f"migration numbering gap: expected {expected_version:03d}, "
                f"found {version} in {path.name}"
            )
            expected_version = version_number
        expected_version += 1

        sql = path.read_text(encoding="utf-8")
        if not sql.strip():
            errors.append(f"empty migration: {path.name}")

        if "DELIMITER" in sql.upper():
            errors.append(
                f"{path.name} uses DELIMITER blocks; migrate.py intentionally "
                "supports ordinary semicolon-terminated SQL only"
            )

        sql_for_checks = strip_comments(sql)

        if UNSUPPORTED_MYSQL.search(sql_for_checks):
            errors.append(
                f"{path.name} uses ALTER TABLE ... ADD ... IF NOT EXISTS; "
                "use INFORMATION_SCHEMA + prepared SQL instead"
            )

        for table in CREATE.findall(sql):
            key = table.lower()
            if key in tables:
                errors.append(
                    f"duplicate CREATE TABLE `{table}` in {path.name}; "
                    f"already created by {created_by[key]}"
                )
            tables.add(key)
            created_by[key] = path.name

        for table in REFERENCES.findall(sql):
            if table.lower() not in tables:
                errors.append(
                    f"foreign key in {path.name} references `{table}` "
                    "before that table is created"
                )

    if files[0].name != "001_create_schema_migrations.sql":
        errors.append("migration 001_create_schema_migrations.sql must be first")

    if errors:
        raise RuntimeError("\n".join(errors))

    return len(files), len(tables)


if __name__ == "__main__":
    count, tables = validate(Path(__file__).resolve().parent.parent / "migrations")
    print(f"Migration validation passed: {count} migrations, {tables} CREATE TABLE targets.")
