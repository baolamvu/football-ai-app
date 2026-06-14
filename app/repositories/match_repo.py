from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.db.models import League, Match, Season, Team


@dataclass
class MatchListFilters:
    league_id: int | None = None
    season_id: int | None = None
    status: str | None = None
    from_date: date | None = None
    to_date: date | None = None


def _match_select():
    home = aliased(Team)
    away = aliased(Team)
    return (
        select(
            Match,
            League.id.label("league_id"),
            League.name.label("league_name"),
            League.code.label("league_code"),
            Season.name.label("season_name"),
            home.canonical_name.label("home_team"),
            away.canonical_name.label("away_team"),
        )
        .join(home, Match.home_team_id == home.id)
        .join(away, Match.away_team_id == away.id)
        .join(Season, Match.season_id == Season.id)
        .join(League, Season.league_id == League.id)
    )


def row_to_dict(row) -> dict:
    match, league_id, league_name, league_code, season_name, home_team, away_team = row
    return {
        "id": match.id,
        "league_id": league_id,
        "league_name": league_name,
        "league_code": league_code,
        "season_name": season_name,
        "season_id": match.season_id,
        "matchweek": match.matchweek,
        "kickoff_at": match.kickoff_at,
        "status": str(match.status),
        "home_team_id": match.home_team_id,
        "home_team": home_team,
        "away_team_id": match.away_team_id,
        "away_team": away_team,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "competition_phase": match.competition_phase,
        "neutral_site": match.neutral_site,
    }


def _apply_filters(stmt, filters: MatchListFilters):
    if filters.league_id is not None:
        stmt = stmt.where(League.id == filters.league_id)
    if filters.season_id is not None:
        stmt = stmt.where(Match.season_id == filters.season_id)
    if filters.status is not None:
        stmt = stmt.where(Match.status == filters.status)
    if filters.from_date is not None:
        start = datetime.combine(filters.from_date, time.min, tzinfo=timezone.utc)
        stmt = stmt.where(Match.kickoff_at >= start)
    if filters.to_date is not None:
        end = datetime.combine(filters.to_date, time.max, tzinfo=timezone.utc)
        stmt = stmt.where(Match.kickoff_at <= end)
    return stmt


def list_matches(db: Session, filters: MatchListFilters | None = None) -> list[dict]:
    filters = filters or MatchListFilters()
    stmt = _apply_filters(_match_select(), filters).order_by(Match.kickoff_at.desc())
    rows = db.execute(stmt).all()
    return [row_to_dict(row) for row in rows]


def get_by_id(db: Session, match_id: int) -> dict | None:
    stmt = _match_select().where(Match.id == match_id)
    row = db.execute(stmt).first()
    if row is None:
        return None
    return row_to_dict(row)
