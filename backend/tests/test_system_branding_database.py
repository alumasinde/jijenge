import os
import unittest

from app.database import db_connection


@unittest.skipUnless(
    os.getenv("RUN_DB_TESTS") == "1",
    "Set RUN_DB_TESTS=1 to run MySQL integration checks against the configured database.",
)
class SystemBrandingDatabaseTests(unittest.TestCase):
    def test_system_and_branding_tables_exist_and_are_seeded(self):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                for table in ("system_settings", "brandings"):
                    cursor.execute(
                        """
                        SELECT COUNT(*) AS table_count
                        FROM information_schema.tables
                        WHERE table_schema = DATABASE() AND table_name = %s
                        """,
                        (table,),
                    )
                    self.assertEqual(cursor.fetchone()["table_count"], 1, table)

                cursor.execute(
                    "SELECT COUNT(*) AS count FROM brandings WHERE brand_code='default'"
                )
                self.assertEqual(cursor.fetchone()["count"], 1)

                cursor.execute(
                    "SELECT COUNT(*) AS count FROM system_settings WHERE is_public=1"
                )
                self.assertGreaterEqual(cursor.fetchone()["count"], 1)
            finally:
                cursor.close()


if __name__ == "__main__":
    unittest.main()
