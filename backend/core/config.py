import os
from pathlib import Path

# Base directory for the project (inside the container or local checkout)
BASE_DIR = Path(os.getenv("BASE_DIR", Path(__file__).resolve().parents[2]))

# Database path (override in container/HA with DB_PATH=/data/db.sqlite)
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "db.sqlite"))

# Playwright user data directories (persist browser sessions & cookies)
FAMLY_PROFILE_DIR = Path(os.getenv("FAMLY_PROFILE_DIR", BASE_DIR / "data" / "famly-profile"))
BABYCONNECT_PROFILE_DIR = Path(os.getenv("BABYCONNECT_PROFILE_DIR", BASE_DIR / "data" / "babyconnect-profile"))

# Headless mode for Playwright (set to "false" in dev to see the browser)
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# Uvicorn / server config
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

# CORS origins for the frontend in dev; in production this can be more strict
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Simple helper for logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "data" / "logs"))
LOG_FILE = Path(os.getenv("LOG_FILE", LOG_DIR / "famly_sync.log"))
