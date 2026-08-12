import unittest
from unittest.mock import patch

from app.config import Settings
from app.Core.middleware import SecurityHeadersMiddleware
from migrate import MIGRATION_PATTERN, load_migrations, split_sql_statements


class SecurityAndMigrationTests(unittest.TestCase):
    def test_migration_names_are_strict(self):
        self.assertIsNotNone(MIGRATION_PATTERN.match("001_create_users.sql"))
        self.assertIsNone(MIGRATION_PATTERN.match("create_users.sql"))
        self.assertIsNone(MIGRATION_PATTERN.match("001_create users.sql"))

    def test_migration_versions_are_unique_and_sorted(self):
        migrations=load_migrations()
        versions=[int(version) for version,_ in migrations]
        self.assertEqual(versions,sorted(versions))
        self.assertEqual(len(versions),len(set(versions)))

    def test_sql_splitter_preserves_semicolons_in_strings(self):
        sql="INSERT INTO t(name) VALUES ('A;B'); SELECT 1;"
        statements=split_sql_statements(sql)
        self.assertEqual(len(statements),2)
        self.assertIn("'A;B'",statements[0])

    def test_production_rejects_debug(self):
        settings=Settings(
            mysql_host="localhost",
            mysql_database="test",
            mysql_user="root",
            mysql_password="x",
            jwt_secret="x"*40,
            app_env="production",
            app_debug=True,
            cors_origins="https://example.com",
        )
        with self.assertRaises(RuntimeError):
            settings.validate_runtime()

    def test_production_rejects_wildcard_cors(self):
        settings=Settings(
            mysql_host="localhost",
            mysql_database="test",
            mysql_user="root",
            mysql_password="x",
            jwt_secret="x"*40,
            app_env="production",
            app_debug=False,
            cors_origins="*",
        )
        with self.assertRaises(RuntimeError):
            settings.validate_runtime()


if __name__=="__main__":
    unittest.main()
