import os


# Test-only defaults so database-independent tests can import application
# modules without requiring a real MySQL server.
#
# These values do not create a database connection. Database integration
# tests remain opt-in via RUN_DB_TESTS=1.

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "false")

os.environ.setdefault("MYSQL_HOST", "127.0.0.1")
os.environ.setdefault("MYSQL_PORT", "3306")
os.environ.setdefault("MYSQL_DATABASE", "test_database")
os.environ.setdefault("MYSQL_USER", "test_user")
os.environ.setdefault("MYSQL_PASSWORD", "test_password")

os.environ.setdefault(
    "JWT_SECRET",
    "test-only-secret-that-is-long-enough-for-testing-1234567890",
)

os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
