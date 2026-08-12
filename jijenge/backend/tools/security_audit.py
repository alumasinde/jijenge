from pathlib import Path
import ast
import re

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"app"

issues=[]

# Detect likely SQL interpolation in execute()/executemany() calls.
# Parameterized SQL such as cursor.execute("... %s", (value,)) is allowed.
for path in APP.rglob("*.py"):
    try:
        tree=ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call):
            continue
        name = node.func.attr if isinstance(node.func,ast.Attribute) else ""
        if name not in {"execute","executemany"} or not node.args:
            continue
        first=node.args[0]
        if isinstance(first,ast.JoinedStr):
            issues.append(
                f"Possible f-string SQL: {path.relative_to(ROOT)}:{node.lineno}"
            )
        if isinstance(first,ast.BinOp) and isinstance(first.op,(ast.Mod,)):
            issues.append(
                f"Possible %-formatted SQL: {path.relative_to(ROOT)}:{node.lineno}"
            )

# Parse every Python source file.
for path in APP.rglob("*.py"):
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        issues.append(f"Syntax error: {path.relative_to(ROOT)}:{exc.lineno}")

# Migration naming and duplicate version audit.
migration_dir=ROOT/"migrations"
versions={}
pattern=re.compile(r"^(\d+)_([A-Za-z0-9_-]+)\.sql$")
for path in migration_dir.glob("*.sql"):
    match=pattern.match(path.name)
    if not match:
        issues.append(f"Invalid migration name: {path.name}")
        continue
    version=match.group(1)
    if version in versions:
        issues.append(f"Duplicate migration version: {version}")
    versions[version]=path.name

if issues:
    print("SECURITY AUDIT: FAILED")
    for issue in issues:
        print("-",issue)
    raise SystemExit(1)

print("SECURITY AUDIT: PASSED")
print(f"Python files checked: {len(list(APP.rglob('*.py')))}")
print(f"Migrations checked: {len(versions)}")
