import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load `.env` from project root before reading os.environ (FastAPI, Alembic, scripts).
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")


def _default_database_url() -> str:
    """Default for local dev; override with DATABASE_URL."""
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "football_ai")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


@lru_cache
def get_database_url() -> str:
    return os.getenv("DATABASE_URL", _default_database_url())
