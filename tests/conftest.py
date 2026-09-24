import os

# Automated tests run without a live PostgreSQL instance unless configured otherwise.
os.environ.setdefault("USE_SQLITE", "True")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-not-production")
os.environ.setdefault("DEBUG", "True")
