
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from migrate import split_sql_statements


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
