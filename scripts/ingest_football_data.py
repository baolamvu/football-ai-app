"""
Lấy dữ liệu từ football-data.org (API v4) và ghi vào PostgreSQL.

Token: đặt trong file `.env` ở thư mục gốc project:
  FOOTBALL_DATA_TOKEN=your_token_here

Chạy (từ thư mục gốc football-ai-app):
  python scripts/ingest_football_data.py --competition PL --season 2023
"""

from __future__ import annotations  # Cho phép dùng kiểu gợi ý hiện đại (dict[str, Any], ...)

import argparse  # Đọc tham số dòng lệnh: --competition, --season
import os  # Đọc biến môi trường (FOOTBALL_DATA_TOKEN sau khi load .env)
import sys  # Thêm đường dẫn project vào Python để import được package `app`
from dataclasses import dataclass  # Tạo class nhẹ để đếm số bản ghi tạo/cập nhật
from datetime import date, datetime  # Xử lý ngày mùa giải và giờ thi đấu
from pathlib import Path  # Tìm đường dẫn file .env và thư mục gốc project
from typing import Any  # Kiểu JSON trả về từ API (dict lồng nhau)

import httpx  # HTTP client gọi API football-data.org
from dotenv import load_dotenv  # Đọc file .env vào os.environ
from sqlalchemy import select  # Viết câu SQL dạng Python (ORM)

# REPO_ROOT = thư mục football-ai-app (cha của thư mục scripts/)
REPO_ROOT = Path(__file__).resolve().parents[1]
# Cho Python import được `app.db.models`, `app.db.session` khi chạy script trực tiếp
sys.path.insert(0, str(REPO_ROOT))
# Nạp biến từ file .env (POSTGRES_*, FOOTBALL_DATA_TOKEN, ...) trước khi dùng os.getenv
load_dotenv(REPO_ROOT / ".env")

from app.db.models import League, Match, Season, SeasonTeamRegistration, Team
from app.db.session import SessionLocal  # Factory tạo phiên làm việc với PostgreSQL

# URL gốc của API v4; các request sẽ nối thêm /competitions/...
API_BASE_URL = "https://api.football-data.org/v4"
# Ghi nhận nguồn dữ liệu trong JSON data_quality_flags của bảng matches
PROVIDER_NAME = "football-data.org"


def get_football_data_token() -> str:
    """
    Lấy token từ biến môi trường FOOTBALL_DATA_TOKEN (đã load từ .env).
    Không cần truyền --token trên dòng lệnh.
    """
    token = os.getenv("FOOTBALL_DATA_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Thiếu FOOTBALL_DATA_TOKEN.\n"
            f"Hãy thêm vào file: {REPO_ROOT / '.env'}\n"
            "Ví dụ: FOOTBALL_DATA_TOKEN=your_token_here"
        )
    return token


@dataclass
class IngestStats:
    """Bộ đếm để in báo cáo sau khi ingest xong."""

    leagues_created: int = 0
    leagues_updated: int = 0
    seasons_created: int = 0
    seasons_updated: int = 0
    teams_created: int = 0
    teams_reused: int = 0
    registrations_created: int = 0
    matches_created: int = 0
    matches_updated: int = 0


class FootballDataClient:
    """Client HTTP gọi football-data.org; tự gắn header X-Auth-Token."""

    def __init__(self, token: str) -> None:
        # httpx.Client tái sử dụng kết nối cho nhiều request trong một lần chạy
        self._client = httpx.Client(
            base_url=API_BASE_URL,  # Mọi path sẽ nối sau URL này
            timeout=30.0,  # Tối đa 30 giây mỗi request
            headers={"X-Auth-Token": token},  # Token từ .env
        )

    def close(self) -> None:
        # Đóng kết nối khi xong (gọi trong finally)
        self._client.close()

    def get_competition(self, code: str) -> dict[str, Any]:
        # Ví dụ: GET /v4/competitions/PL → tên giải, mã, quốc gia
        response = self._client.get(f"/competitions/{code}")
        response.raise_for_status()  # Ném lỗi nếu HTTP 4xx/5xx
        return response.json()  # Parse JSON thành dict Python

    def get_competition_matches(self, code: str, season: int) -> dict[str, Any]:
        # Ví dụ: GET /v4/competitions/PL/matches?season=2023 → danh sách trận
        response = self._client.get(
            f"/competitions/{code}/matches",
            params={"season": season},  # Query string ?season=2023
        )
        response.raise_for_status()
        return response.json()


def parse_args() -> argparse.Namespace:
    """Đọc tham số từ dòng lệnh (không còn --token)."""
    parser = argparse.ArgumentParser(
        description="Ingest dữ liệu mùa giải từ football-data.org vào PostgreSQL.",
    )
    parser.add_argument(
        "--competition",
        default="PL",
        help="Mã giải trên football-data (PL=Premier League, BL1, PD, ...).",
    )
    parser.add_argument(
        "--season",
        type=int,
        required=True,
        help="Năm bắt đầu mùa giải, ví dụ 2023 cho mùa 2023-24.",
    )
    return parser.parse_args()


def parse_utc_datetime(value: str) -> datetime:
    """Chuyển chuỗi ISO từ API (có chữ Z) sang datetime có timezone UTC."""
    # API trả "2023-08-11T19:00:00Z" → Python cần "+00:00" thay cho "Z"
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def map_match_status(provider_status: str) -> str:
    """
    Map trạng thái API (FINISHED, SCHEDULED, ...) sang enum trong DB
    (finished, scheduled, live, postponed, cancelled).
    """
    status = provider_status.upper()
    if status in {"SCHEDULED", "TIMED"}:
        return "scheduled"
    if status in {"IN_PLAY", "PAUSED"}:
        return "live"
    if status in {"FINISHED", "AWARDED"}:
        return "finished"
    if status in {"POSTPONED", "SUSPENDED"}:
        return "postponed"
    if status in {"CANCELLED"}:
        return "cancelled"
    return "scheduled"  # Mặc định an toàn nếu API thêm status mới


def get_or_create_league(db: Any, payload: dict[str, Any], stats: IngestStats) -> League:
    """Tìm league theo code (PL); chưa có thì INSERT, có rồi thì cập nhật tên/quốc gia."""
    code = payload["code"]  # VD: "PL"
    # SELECT ... WHERE code = 'PL' LIMIT 1
    league = db.scalars(select(League).where(League.code == code)).first()
    name = payload["name"]  # VD: "Premier League"
    country = (payload.get("area") or {}).get("name")  # VD: "England"

    if league is None:
        league = League(code=code, name=name, country=country, tier=1)
        db.add(league)  # Đưa vào session (chưa COMMIT)
        db.flush()  # Gửi INSERT để lấy league.id ngay (cần cho bảng seasons)
        stats.leagues_created += 1
        return league

    # League đã tồn tại: đồng bộ tên/quốc gia nếu API đổi
    changed = False
    if league.name != name:
        league.name = name
        changed = True
    if league.country != country:
        league.country = country
        changed = True
    if changed:
        stats.leagues_updated += 1
    return league


def get_or_create_season(
    db: Any,
    league_id: int,
    season_year: int,
    competition_payload: dict[str, Any],
    matches_payload: dict[str, Any],
    stats: IngestStats,
) -> Season:
    """Tạo hoặc cập nhật một mùa giải (VD: 2023-24) thuộc league_id."""
    # Ưu tiên metadata mùa từ response matches, fallback sang competition
    season_node = matches_payload.get("season") or competition_payload.get("currentSeason") or {}
    start_date = date.fromisoformat(season_node["startDate"])  # "2023-08-11" → date
    end_date = date.fromisoformat(season_node["endDate"])
    current_matchday = season_node.get("currentMatchday")  # Vòng hiện tại (nếu có)
    # season_year=2023 → tên hiển thị "2023-24"
    season_name = f"{season_year}-{str((season_year + 1) % 100).zfill(2)}"

    season = db.scalars(
        select(Season).where(
            Season.league_id == league_id,
            Season.name == season_name,
        )
    ).first()

    if season is None:
        season = Season(
            league_id=league_id,
            name=season_name,
            start_date=start_date,
            end_date=end_date,
            matchweeks=current_matchday,
        )
        db.add(season)
        db.flush()  # Lấy season.id cho các bảng con
        stats.seasons_created += 1
        return season

    changed = False
    if season.start_date != start_date:
        season.start_date = start_date
        changed = True
    if season.end_date != end_date:
        season.end_date = end_date
        changed = True
    if current_matchday and season.matchweeks != current_matchday:
        season.matchweeks = current_matchday
        changed = True
    if changed:
        stats.seasons_updated += 1
    return season


def get_or_create_team(
    db: Any,
    team_name: str,
    stats: IngestStats,
    team_cache: dict[str, Team],
) -> Team:
    """
    Tìm đội theo tên chuẩn (canonical_name).
    Dùng team_cache vì SessionLocal có autoflush=False — tránh INSERT trùng trong cùng lần chạy.
    """
    team = team_cache.get(team_name)
    if team:
        stats.teams_reused += 1
        return team

    team = db.scalars(select(Team).where(Team.canonical_name == team_name)).first()
    if team:
        team_cache[team_name] = team
        stats.teams_reused += 1
        return team

    team = Team(canonical_name=team_name)
    db.add(team)
    db.flush()  # Lấy team.id
    team_cache[team_name] = team
    stats.teams_created += 1
    return team


def ensure_registration(
    db: Any,
    season_id: int,
    team_id: int,
    stats: IngestStats,
    registration_cache: set[tuple[int, int]],
) -> None:
    """
    Ghi đội tham gia mùa giải (bảng season_team_registration).
    Mỗi cặp (season_id, team_id) chỉ một dòng — dùng cache tránh vi phạm UNIQUE.
    """
    key = (season_id, team_id)
    if key not in registration_cache:
        db.add(SeasonTeamRegistration(season_id=season_id, team_id=team_id))
        registration_cache.add(key)
        stats.registrations_created += 1


def upsert_match(
    db: Any,
    season_id: int,
    home_team_id: int,
    away_team_id: int,
    match_payload: dict[str, Any],
    stats: IngestStats,
    match_cache: dict[tuple[int, datetime, int, int], Match],
) -> None:
    """
    upsert = update hoặc insert.
    Khóa logic: cùng mùa + giờ đá + đội nhà + đội khách → cùng một trận.
    """
    kickoff_at = parse_utc_datetime(match_payload["utcDate"])
    provider_status = match_payload.get("status", "SCHEDULED")
    mapped_status = map_match_status(provider_status)
    score = match_payload.get("score") or {}
    full_time = score.get("fullTime") or {}  # Tỉ số hiệp chính (có thể null nếu chưa đá)
    provider_match_id = match_payload.get("id")  # ID trên football-data (lưu vào JSON flags)

    cache_key = (season_id, kickoff_at, home_team_id, away_team_id)
    existing = match_cache.get(cache_key)

    if existing is None:
        existing = db.scalars(
            select(Match).where(
                Match.season_id == season_id,
                Match.kickoff_at == kickoff_at,
                Match.home_team_id == home_team_id,
                Match.away_team_id == away_team_id,
            )
        ).first()
        if existing is not None:
            match_cache[cache_key] = existing

    # Metadata nguồn — hữu ích khi sau này ghép Understat
    data_quality_flags = {
        "provider": PROVIDER_NAME,
        "provider_match_id": provider_match_id,
        "provider_last_updated": match_payload.get("lastUpdated"),
    }

    if existing is None:
        row = Match(
            season_id=season_id,
            matchweek=match_payload.get("matchday"),
            kickoff_at=kickoff_at,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            status=mapped_status,
            competition_phase=match_payload.get("stage"),
            match_round=match_payload.get("group"),
            home_score=full_time.get("home"),
            away_score=full_time.get("away"),
            data_quality_flags=data_quality_flags,
        )
        db.add(row)
        match_cache[cache_key] = row
        stats.matches_created += 1
        return

    # Trận đã có: cập nhật điểm/trạng thái (chạy lại script vẫn an toàn)
    existing.matchweek = match_payload.get("matchday")
    existing.status = mapped_status
    existing.competition_phase = match_payload.get("stage")
    existing.match_round = match_payload.get("group")
    existing.home_score = full_time.get("home")
    existing.away_score = full_time.get("away")
    existing.data_quality_flags = data_quality_flags
    stats.matches_updated += 1


def ingest(competition: str, season_year: int, token: str) -> IngestStats:
    """Luồng chính: gọi API → map dữ liệu → ghi DB → commit."""
    stats = IngestStats()
    client = FootballDataClient(token=token)
    db = SessionLocal()  # Mở một phiên SQLAlchemy
    try:
        competition_payload = client.get_competition(competition)
        matches_payload = client.get_competition_matches(competition, season_year)
        all_matches = matches_payload.get("matches") or []

        league = get_or_create_league(db, competition_payload, stats)
        season = get_or_create_season(
            db=db,
            league_id=league.id,
            season_year=season_year,
            competition_payload=competition_payload,
            matches_payload=matches_payload,
            stats=stats,
        )

        team_cache: dict[str, Team] = {}
        # Nạp sẵn các đăng ký đội-mùa đã có (khi chạy lại script)
        registration_cache = set(
            db.execute(
                select(
                    SeasonTeamRegistration.season_id,
                    SeasonTeamRegistration.team_id,
                ).where(SeasonTeamRegistration.season_id == season.id)
            ).all()
        )
        existing_matches = db.scalars(select(Match).where(Match.season_id == season.id)).all()
        match_cache = {
            (m.season_id, m.kickoff_at, m.home_team_id, m.away_team_id): m
            for m in existing_matches
        }

        for row in all_matches:
            home_name = row["homeTeam"]["name"]
            away_name = row["awayTeam"]["name"]
            home_team = get_or_create_team(db, home_name, stats, team_cache)
            away_team = get_or_create_team(db, away_name, stats, team_cache)
            ensure_registration(db, season.id, home_team.id, stats, registration_cache)
            ensure_registration(db, season.id, away_team.id, stats, registration_cache)
            upsert_match(
                db=db,
                season_id=season.id,
                home_team_id=home_team.id,
                away_team_id=away_team.id,
                match_payload=row,
                stats=stats,
                match_cache=match_cache,
            )

        db.commit()  # Ghi tất cả thay đổi xuống PostgreSQL
        return stats
    except Exception:
        db.rollback()  # Lỗi giữa chừng → hủy transaction, DB không bị dở dang
        raise
    finally:
        db.close()  # Luôn đóng session
        client.close()  # Luôn đóng HTTP client


def main() -> None:
    args = parse_args()
    token = get_football_data_token()  # Đọc từ .env — không cần --token

    stats = ingest(
        competition=args.competition,
        season_year=args.season,
        token=token,
    )
    print("Ingest complete:")
    print(f"  leagues: created={stats.leagues_created} updated={stats.leagues_updated}")
    print(f"  seasons: created={stats.seasons_created} updated={stats.seasons_updated}")
    print(f"  teams: created={stats.teams_created} reused={stats.teams_reused}")
    print(f"  registrations created={stats.registrations_created}")
    print(f"  matches: created={stats.matches_created} updated={stats.matches_updated}")


if __name__ == "__main__":
    # Chỉ chạy main() khi gọi trực tiếp: python scripts/ingest_football_data.py ...
    main()
