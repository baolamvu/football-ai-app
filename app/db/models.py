"""SQLAlchemy ORM models mirroring db/schema/001_core_schema.sql."""

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func, text

from app.db.base import Base

# PostgreSQL enums already created by 001_core_schema.sql — do not recreate in ORM.
match_status_enum = PG_ENUM(
    "scheduled",
    "live",
    "finished",
    "postponed",
    "cancelled",
    name="match_status",
    create_type=False,
)

team_side_enum = PG_ENUM("home", "away", name="team_side", create_type=False)


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[Optional[str]] = mapped_column(Text)
    tier: Mapped[Optional[int]] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("leagues.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    matchweeks: Mapped[Optional[int]] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("league_id", "name", name="seasons_league_id_name_key"),)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    founded_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class SeasonTeamRegistration(Base):
    __tablename__ = "season_team_registration"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("season_id", "team_id", name="season_team_registration_season_id_team_id_key"),
    )


class Referee(Base):
    __tablename__ = "referees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    league_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("leagues.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    matchweek: Mapped[Optional[int]] = mapped_column(SmallInteger)
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    home_team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    away_team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        match_status_enum,
        nullable=False,
        server_default=text("'scheduled'::match_status"),
    )
    venue_lat: Mapped[Optional[float]] = mapped_column(Float)
    venue_lon: Mapped[Optional[float]] = mapped_column(Float)
    neutral_site: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    competition_phase: Mapped[Optional[str]] = mapped_column(Text)
    match_round: Mapped[Optional[str]] = mapped_column("round", Text)
    referee_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("referees.id", ondelete="SET NULL")
    )
    home_score: Mapped[Optional[int]] = mapped_column(SmallInteger)
    away_score: Mapped[Optional[int]] = mapped_column(SmallInteger)
    home_corners: Mapped[Optional[int]] = mapped_column(SmallInteger)
    away_corners: Mapped[Optional[int]] = mapped_column(SmallInteger)
    home_yellows: Mapped[Optional[int]] = mapped_column(SmallInteger)
    away_yellows: Mapped[Optional[int]] = mapped_column(SmallInteger)
    home_reds: Mapped[Optional[int]] = mapped_column(SmallInteger)
    away_reds: Mapped[Optional[int]] = mapped_column(SmallInteger)
    data_quality_flags: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("home_team_id <> away_team_id", name="chk_matches_teams_different"),
    )


class TeamMatchStat(Base):
    __tablename__ = "team_match_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    side: Mapped[str] = mapped_column(team_side_enum, nullable=False)
    xg: Mapped[Optional[float]] = mapped_column(Float)
    xga: Mapped[Optional[float]] = mapped_column(Float)
    shots: Mapped[Optional[int]] = mapped_column(SmallInteger)
    sot: Mapped[Optional[int]] = mapped_column(SmallInteger)
    possession: Mapped[Optional[float]] = mapped_column(Float)
    corners_for: Mapped[Optional[int]] = mapped_column(SmallInteger)
    fouls: Mapped[Optional[int]] = mapped_column(SmallInteger)
    yellows: Mapped[Optional[int]] = mapped_column(SmallInteger)
    reds: Mapped[Optional[int]] = mapped_column(SmallInteger)
    ppda_proxy: Mapped[Optional[float]] = mapped_column(Float)
    passes_into_box: Mapped[Optional[int]] = mapped_column(SmallInteger)
    progressive_passes: Mapped[Optional[int]] = mapped_column(SmallInteger)
    high_turnovers: Mapped[Optional[int]] = mapped_column(SmallInteger)
    avg_def_line_height_proxy: Mapped[Optional[float]] = mapped_column(Float)
    tactical_profile_vector: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    source: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("match_id", "team_id", name="team_match_stats_match_id_team_id_key"),
    )


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="SET NULL")
    )
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    xg_contrib: Mapped[Optional[float]] = mapped_column(Float)
    shots: Mapped[Optional[int]] = mapped_column(SmallInteger)
    cards: Mapped[Optional[int]] = mapped_column(SmallInteger)
    rating_proxy: Mapped[Optional[float]] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="player_match_stats_match_id_player_id_key"),
    )


class MatchEvent(Base):
    __tablename__ = "match_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    minute: Mapped[Optional[int]] = mapped_column(SmallInteger)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class StandingsSnapshot(Base):
    __tablename__ = "standings_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    matchweek: Mapped[Optional[int]] = mapped_column(SmallInteger)
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    points: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    goals_for: Mapped[Optional[int]] = mapped_column(SmallInteger)
    goals_against: Mapped[Optional[int]] = mapped_column(SmallInteger)
    played: Mapped[Optional[int]] = mapped_column(SmallInteger)
    title_prob_proxy: Mapped[Optional[float]] = mapped_column(Float)
    source: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint(
            "season_id",
            "team_id",
            "snapshot_at",
            name="standings_snapshots_season_id_team_id_snapshot_at_key",
        ),
    )


class MatchContext(Base):
    __tablename__ = "match_context"

    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
    )
    derby_match_indicator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    rivalry_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0"))
    revenge_match_indicator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    big_match_indicator: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    travel_km_away_team: Mapped[Optional[float]] = mapped_column(Float)
    travel_km_home_team: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Injury(Base):
    __tablename__ = "injuries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    severity: Mapped[Optional[int]] = mapped_column(SmallInteger)
    expected_return: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Suspension(Base):
    __tablename__ = "suspensions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    from_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    to_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)


class PlayerImportanceWeight(Base):
    __tablename__ = "player_importance_weights"

    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.id", ondelete="CASCADE"), primary_key=True
    )
    season_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("seasons.id", ondelete="CASCADE"), primary_key=True
    )
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class EloRatingHistory(Base):
    __tablename__ = "elo_rating_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    season_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("seasons.id", ondelete="SET NULL")
    )
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    rating_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)


class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    dtype: Mapped[str] = mapped_column(Text, nullable=False)
    leakage_notes: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (UniqueConstraint("name", "version", name="feature_definitions_name_version_key"),)


class MatchFeatureSet(Base):
    __tablename__ = "match_feature_sets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    pipeline_version: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    feature_vector: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    schema_hash: Mapped[Optional[str]] = mapped_column(Text)
    is_training_eligible: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    debug_trace: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)

    __table_args__ = (
        UniqueConstraint(
            "match_id",
            "pipeline_version",
            name="match_feature_sets_match_id_pipeline_version_key",
        ),
    )


class TrainingDatasetManifest(Base):
    __tablename__ = "training_dataset_manifests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sql_query_hash: Mapped[Optional[str]] = mapped_column(Text)
    row_count: Mapped[Optional[int]] = mapped_column(BigInteger)
    min_kickoff: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    max_kickoff: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    label_version: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class TrainingExample(Base):
    __tablename__ = "training_examples"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    manifest_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("training_dataset_manifests.id", ondelete="CASCADE"), nullable=False
    )
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    labels: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    split_tag: Mapped[Optional[str]] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("manifest_id", "match_id", name="training_examples_manifest_id_match_id_key"),
    )


class MLModel(Base):
    __tablename__ = "ml_models"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    framework: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_uri: Mapped[Optional[str]] = mapped_column(Text)
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    model_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ml_models.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    probs: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    extras: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    calibration_version: Mapped[Optional[str]] = mapped_column(Text)


class PredictionExplanation(Base):
    __tablename__ = "prediction_explanations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prediction_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False
    )
    llm_model: Mapped[str] = mapped_column(Text, nullable=False)
    structured_facts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    explanation_text: Mapped[Optional[str]] = mapped_column(Text)
    safety_flags: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
