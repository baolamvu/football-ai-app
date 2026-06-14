"""
Insert sample Premier League data (idempotent on league code EPL).

Run from repo root: python scripts/seed_sample.py
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(REPO_ROOT / ".env")

from sqlalchemy import select

from app.db.models import (
    League,
    MLModel,
    Match,
    Prediction,
    Season,
    SeasonTeamRegistration,
    Team,
    TeamMatchStat,
)
from app.db.session import SessionLocal

LEAGUE_CODE = "EPL"


def main() -> None:
    db = SessionLocal()
    try:
        league = db.scalars(select(League).where(League.code == LEAGUE_CODE)).first()
        if league:
            print(f"Sample data already present (league {LEAGUE_CODE!r}, id={league.id}). Skipping.")
            return

        print("Seeding sample data...")
        league = League(code=LEAGUE_CODE, name="Premier League", country="England", tier=1)
        db.add(league)
        db.flush()

        season = Season(
            league_id=league.id,
            name="2024-25",
            start_date=date(2024, 8, 1),
            end_date=date(2025, 5, 31),
            matchweeks=38,
        )
        db.add(season)
        db.flush()

        team_names = ["Arsenal", "Chelsea", "Liverpool", "Manchester City"]
        teams = {}
        for name in team_names:
            t = Team(canonical_name=name)
            db.add(t)
            db.flush()
            teams[name] = t
            db.add(SeasonTeamRegistration(season_id=season.id, team_id=t.id))

        def utc(y, m, d, h=15, mi=0):
            return datetime(y, m, d, h, mi, tzinfo=timezone.utc)

        # Finished matches (for form stats)
        m1 = Match(
            season_id=season.id,
            matchweek=1,
            kickoff_at=utc(2024, 8, 17),
            home_team_id=teams["Arsenal"].id,
            away_team_id=teams["Chelsea"].id,
            status="finished",
            home_score=2,
            away_score=1,
        )
        m2 = Match(
            season_id=season.id,
            matchweek=1,
            kickoff_at=utc(2024, 8, 18),
            home_team_id=teams["Liverpool"].id,
            away_team_id=teams["Manchester City"].id,
            status="finished",
            home_score=1,
            away_score=1,
        )
        m3 = Match(
            season_id=season.id,
            matchweek=2,
            kickoff_at=utc(2024, 8, 24),
            home_team_id=teams["Chelsea"].id,
            away_team_id=teams["Liverpool"].id,
            status="finished",
            home_score=0,
            away_score=2,
        )
        # Upcoming
        m4 = Match(
            season_id=season.id,
            matchweek=10,
            kickoff_at=utc(2025, 11, 2),
            home_team_id=teams["Arsenal"].id,
            away_team_id=teams["Manchester City"].id,
            status="scheduled",
        )
        for m in (m1, m2, m3, m4):
            db.add(m)
        db.flush()

        def add_stats(match: Match, home_xg: float, away_xg: float):
            db.add(
                TeamMatchStat(
                    match_id=match.id,
                    team_id=match.home_team_id,
                    side="home",
                    xg=home_xg,
                    xga=away_xg,
                    shots=12,
                    sot=5,
                    possession=55.0,
                    corners_for=6,
                )
            )
            db.add(
                TeamMatchStat(
                    match_id=match.id,
                    team_id=match.away_team_id,
                    side="away",
                    xg=away_xg,
                    xga=home_xg,
                    shots=10,
                    sot=4,
                    possession=45.0,
                    corners_for=4,
                )
            )

        add_stats(m1, 1.8, 1.1)
        add_stats(m2, 1.2, 1.3)
        add_stats(m3, 0.6, 2.1)

        model = MLModel(
            name="baseline_form_v1",
            framework="baseline",
            active=True,
            metrics={"type": "rolling_goals_form"},
        )
        db.add(model)
        db.flush()

        db.add(
            Prediction(
                match_id=m4.id,
                model_id=model.id,
                probs={"home_win": 42.0, "draw": 28.0, "away_win": 30.0},
                extras={"seeded": True},
            )
        )

        db.commit()
        print("Seed complete:")
        print(f"  league_id={league.id} season_id={season.id}")
        print(f"  teams={len(team_names)} matches=4 (3 finished, 1 scheduled)")
        print(f"  model={model.name} pre-seeded prediction for match_id={m4.id}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
