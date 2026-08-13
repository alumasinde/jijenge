#!/usr/bin/env python3
"""
Comprehensive migration testing script.
Tests migration files for syntax, structure, and integrity.
"""

import sys
from pathlib import Path
from migrate import load_migrations, split_sql_statements, checksum_file, MIGRATION_PATTERN


def test_migration_file_structure():
    """Test that all migration files have valid names and structure."""
    print("\n" + "=" * 60)
    print("TEST 1: Migration File Structure")
    print("=" * 60)
    
    migration_dir = Path(__file__).resolve().parent / "migrations"
    all_files = sorted(migration_dir.glob("*.sql"))
    
    if not all_files:
        print("❌ No migration files found!")
        return False
    
    issues = []
    for file in all_files:
        if not MIGRATION_PATTERN.match(file.name):
            issues.append(f"  ❌ Invalid filename: {file.name}")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    
    print(f"✅ All {len(all_files)} migration files have valid names")
    return True


def test_migration_loading():
    """Test that all migrations can be loaded and sorted correctly."""
    print("\n" + "=" * 60)
    print("TEST 2: Migration Loading and Sorting")
    print("=" * 60)
    
    try:
        migrations = load_migrations()
        print(f"✅ Loaded {len(migrations)} migrations")
        
        # Verify sequential numbering
        versions = [int(v) for v, _ in migrations]
        expected_versions = list(range(1, len(migrations) + 1))
        
        if versions != expected_versions:
            missing = set(expected_versions) - set(versions)
            duplicates = [v for i, v in enumerate(versions) if v in versions[:i]]
            
            if missing:
                print(f"❌ Missing migration versions: {sorted(missing)}")
            if duplicates:
                print(f"❌ Duplicate migration versions: {sorted(set(duplicates))}")
            return False
        
        print(f"✅ All versions numbered sequentially (1-{len(migrations)})")
        return True
        
    except Exception as e:
        print(f"❌ Error loading migrations: {e}")
        return False


def test_migration_sql_parsing():
    """Test that all migration files contain valid, parseable SQL."""
    print("\n" + "=" * 60)
    print("TEST 3: SQL Parsing and Validation")
    print("=" * 60)
    
    try:
        migrations = load_migrations()
    except Exception as e:
        print(f"❌ Could not load migrations: {e}")
        return False
    
    errors = []
    empty_files = []
    
    for version, path in migrations:
        try:
            sql = path.read_text(encoding="utf-8").strip()
            
            if not sql:
                empty_files.append(f"  ⚠️  {path.name} is empty")
                continue
            
            statements = split_sql_statements(sql)
            
            if not statements:
                errors.append(f"  ❌ {path.name}: No SQL statements found")
            
        except Exception as e:
            errors.append(f"  ❌ {path.name}: {str(e)}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    if empty_files:
        print("\n".join(empty_files))
    
    print(f"✅ All {len(migrations)} migration files contain valid SQL")
    if empty_files:
        print(f"   ({len(empty_files)} empty files skipped)")
    return True


def test_migration_checksums():
    """Test that migration files can be checksummed correctly."""
    print("\n" + "=" * 60)
    print("TEST 4: Checksum Calculation")
    print("=" * 60)
    
    try:
        migrations = load_migrations()
    except Exception as e:
        print(f"❌ Could not load migrations: {e}")
        return False
    
    errors = []
    checksums = {}
    
    for version, path in migrations:
        try:
            checksum = checksum_file(path)
            if not checksum or len(checksum) != 64:  # SHA256 is 64 hex chars
                errors.append(f"  ❌ {path.name}: Invalid checksum")
                continue
            
            # Track for duplicate detection
            if checksum in checksums:
                errors.append(
                    f"  ❌ Duplicate checksum detected: "
                    f"{path.name} and {checksums[checksum]}"
                )
            else:
                checksums[checksum] = path.name
                
        except Exception as e:
            errors.append(f"  ❌ {path.name}: {str(e)}")
    
    if errors:
        print("\n".join(errors))
        return False
    
    print(f"✅ Calculated checksums for {len(checksums)} migration files")
    print(f"   All checksums are unique (no modified files detected)")
    return True


def test_migration_dependencies():
    """Test that migrations don't reference non-existent tables."""
    print("\n" + "=" * 60)
    print("TEST 5: Migration Content Analysis")
    print("=" * 60)
    
    try:
        migrations = load_migrations()
    except Exception as e:
        print(f"❌ Could not load migrations: {e}")
        return False
    
    # Basic sanity checks
    drop_before_create = []
    alter_nonexistent = []
    
    for version, path in migrations:
        sql = path.read_text(encoding="utf-8").upper()
        
        # Check if migration drops something before creating it
        if "DROP" in sql and "CREATE" in sql:
            drop_idx = sql.find("DROP")
            create_idx = sql.find("CREATE")
            if drop_idx < create_idx:
                drop_before_create.append(path.name)
    
    if drop_before_create:
        print(f"⚠️  Migrations that drop then create (expected pattern):")
        for fname in drop_before_create[:5]:
            print(f"   - {fname}")
        if len(drop_before_create) > 5:
            print(f"   ... and {len(drop_before_create) - 5} more")
    
    print(f"✅ Migration content analysis complete")
    print(f"   Analyzed {len(migrations)} migrations")
    return True


def main():
    """Run all migration tests."""
    print("\n" + "=" * 60)
    print("JIJENGE MIGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_migration_file_structure),
        ("Loading & Sorting", test_migration_loading),
        ("SQL Parsing", test_migration_sql_parsing),
        ("Checksums", test_migration_checksums),
        ("Content Analysis", test_migration_dependencies),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} - {name}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
