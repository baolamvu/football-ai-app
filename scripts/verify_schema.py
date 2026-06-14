"""
Verify PostgreSQL schema: expected tables, enums, alembic version.

Run from repo root: python scripts/verify_schema.py
Exit code 0 if OK, 1 if repair failed or schema incomplete.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from sqlalchemy import text

from app.db.session import engine

# Tables from db/schema/001_core_schema.sql (CREATE TABLE)
EXPECTED_TABLES = sorted(
    [
        "elo_rating_history",
        "feature_definitions",
        "injuries",
        "leagues",
        "match_context",
        "match_events",
        "match_feature_sets",
        "matches",
        "ml_models",
        "player_importance_weights",
        "player_match_stats",
        "players",
        "prediction_explanations",
        "predictions",
        "referees",
        "season_team_registration",
        "seasons",
        "standings_snapshots",
        "suspensions",
        "team_match_stats",
        "teams",
        "training_dataset_manifests",
        "training_examples",
    ]
)

EXPECTED_ENUMS = ["match_status", "team_side"]


def _fetch_tables(conn) -> set[str]:
    rows = conn.execute(
        text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
    ).fetchall()
    return {r[0] for r in rows}


def _fetch_enums(conn) -> set[str]:
    rows = conn.execute(
        text(
            """
            SELECT t.typname
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public' AND t.typtype = 'e'
            """
        )
    ).fetchall()
    return {r[0] for r in rows}


def _alembic_version(conn) -> str | None:
    if "alembic_version" not in _fetch_tables(conn):
        return None
    return conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()


def main() -> int:
    print("=== Database schema verification ===\n")

    try:
        with engine.connect() as conn:
            tables = _fetch_tables(conn)
            enums = _fetch_enums(conn)
            alembic = _alembic_version(conn)
    except Exception as e:
        print(f"[FAIL] Cannot connect: {e}")
        print("\n[FIX] Check .env, PostgreSQL running, run: python scripts/init_database.py")
        return 1

    missing_tables = sorted(set(EXPECTED_TABLES) - tables)
    extra_tables = sorted(tables - set(EXPECTED_TABLES) - {"alembic_version"})

    print(f"Tables in public schema: {len(tables)}")
    print(f"Expected application tables: {len(EXPECTED_TABLES)}")
    print(f"Missing tables: {missing_tables or '(none)'}")
    print(f"Extra tables (ignored alembic_version): {extra_tables or '(none)'}")

    missing_enums = sorted(set(EXPECTED_ENUMS) - enums)
    print(f"\nEnums found: {sorted(enums)}")
    print(f"Missing enums: {missing_enums or '(none)'}")
    print(f"\nAlembic version_num: {alembic or '(table missing — run: alembic stamp head)'}")

    ok = not missing_tables and not missing_enums

    if ok:
        print("\n[OK] Schema looks complete.")
        return 0

    print("\n[WARN] Schema incomplete — attempting repair via init_database.py ...")
    import subprocess

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "init_database.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print("[FAIL] init_database.py failed (DB may already exist with partial schema).")
        return 1

    with engine.connect() as conn:
        tables = _fetch_tables(conn)
        missing_tables = sorted(set(EXPECTED_TABLES) - tables)

    if missing_tables:
        print(f"[FAIL] Still missing after repair: {missing_tables}")
        return 1

    print("[OK] Repair succeeded; schema complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
