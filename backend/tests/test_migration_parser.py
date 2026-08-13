
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from migrate import checksum_file, get_pending_migrations, split_sql_statements


def test_pending_migrations_use_each_file_checksum(tmp_path):
    first = tmp_path / "001_first.sql"
    second = tmp_path / "002_second.sql"
    first.write_text("CREATE TABLE first (id INT);", encoding="utf-8")
    second.write_text("CREATE TABLE second (id INT);", encoding="utf-8")

    pending = get_pending_migrations(
        [("001", first), ("002", second)],
        {},
    )

    assert [item[2] for item in pending] == [
        checksum_file(first),
        checksum_file(second),
    ]
    assert pending[0][2] != pending[1][2]


def test_split_sql_respects_strings():
    sql = """
    INSERT INTO example (value) VALUES ('hello;world');
    CREATE TABLE example2 (id INT NOT NULL);
    """
    statements = split_sql_statements(sql)
    assert len(statements) == 2
    assert "hello;world" in statements[0]


def test_split_sql_removes_comments():
    sql = """
    # comment;
    CREATE TABLE a (id INT);
    -- another comment;
    CREATE TABLE b (id INT);
    """
    statements = split_sql_statements(sql)
    assert len(statements) == 2
