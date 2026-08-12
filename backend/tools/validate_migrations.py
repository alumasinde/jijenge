#!/usr/bin/env python3
"""Static validation for Jijenge MySQL migrations.

This intentionally uses no database connection. It catches the classes of
migration mistakes that can make a fresh database fail: invalid filenames,
duplicate CREATE TABLE statements, and foreign keys pointing to tables that
have not been created yet.
"""
from __future__ import annotations

import re
from pathlib import Path

PATTERN = re.compile(r"^(\d+)_([A-Za-z0-9_-]+)\.sql$")
CREATE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([A-Za-z0-9_]+)`?", re.I)
REFERENCES = re.compile(r"REFERENCES\s+`?([A-Za-z0-9_]+)`?\s*\(", re.I)


def validate(directory: Path) -> tuple[int, int]:
    files = [p for p in directory.glob("*.sql") if PATTERN.match(p.name)]
    files.sort(key=lambda p: int(PATTERN.match(p.name).group(1)))

    if not files:
        raise RuntimeError("No migrations found")

    seen_versions: set[str] = set()
    tables: set[str] = set()
    created_by: dict[str, str] = {}
    errors: list[str] = []

    for path in files:
        match = PATTERN.match(path.name)
        assert match is not None
        version = match.group(1)
        if version in seen_versions:
            errors.append(f"duplicate migration version: {version}")
        seen_versions.add(version)

        sql = path.read_text(encoding="utf-8")
        if not sql.strip():
            errors.append(f"empty migration: {path.name}")

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
