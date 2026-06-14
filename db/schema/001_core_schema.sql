-- =============================================================================
-- Football AI Platform — Core PostgreSQL schema (v1)
-- Run after: CREATE DATABASE football_ai; \c football_ai;
-- =============================================================================

BEGIN;

CREATE TYPE match_status AS ENUM (
  'scheduled',
  'live',
  'finished',
  'postponed',
  'cancelled'
);

CREATE TYPE team_side AS ENUM ('home', 'away');

CREATE TABLE leagues (
  id           BIGSERIAL PRIMARY KEY,
  code         TEXT NOT NULL UNIQUE,
  name         TEXT NOT NULL,
  country      TEXT,
  tier         SMALLINT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE seasons (
  id           BIGSERIAL PRIMARY KEY,
  league_id    BIGINT NOT NULL REFERENCES leagues (id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  start_date   DATE NOT NULL,
  end_date     DATE NOT NULL,
  matchweeks   SMALLINT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (league_id, name)
);

CREATE TABLE teams (
  id               BIGSERIAL PRIMARY KEY,
  canonical_name   TEXT NOT NULL,
  founded_year     SMALLINT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE season_team_registration (
  id          BIGSERIAL PRIMARY KEY,
  season_id   BIGINT NOT NULL REFERENCES seasons (id) ON DELETE CASCADE,
  team_id     BIGINT NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  UNIQUE (season_id, team_id)
);

CREATE TABLE referees (
  id               BIGSERIAL PRIMARY KEY,
  display_name     TEXT NOT NULL,
  league_id        BIGINT REFERENCES leagues (id) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE matches (
  id                   BIGSERIAL PRIMARY KEY,
  season_id            BIGINT NOT NULL REFERENCES seasons (id) ON DELETE CASCADE,
  matchweek            SMALLINT,
  kickoff_at           TIMESTAMPTZ NOT NULL,
  home_team_id         BIGINT NOT NULL REFERENCES teams (id) ON DELETE RESTRICT,
  away_team_id         BIGINT NOT NULL REFERENCES teams (id) ON DELETE RESTRICT,
  status               match_status NOT NULL DEFAULT 'scheduled',
  venue_lat            DOUBLE PRECISION,
  venue_lon            DOUBLE PRECISION,
  neutral_site         BOOLEAN NOT NULL DEFAULT FALSE,
  competition_phase    TEXT,
  round                TEXT,
  referee_id           BIGINT REFERENCES referees (id) ON DELETE SET NULL,
  home_score           SMALLINT,
  away_score           SMALLINT,
  home_corners         SMALLINT,
  away_corners         SMALLINT,
  home_yellows         SMALLINT,
  away_yellows         SMALLINT,
  home_reds            SMALLINT,
  away_reds            SMALLINT,
  data_quality_flags   JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_matches_teams_different CHECK (home_team_id <> away_team_id)
);

CREATE TABLE team_match_stats (
  id                         BIGSERIAL PRIMARY KEY,
  match_id                   BIGINT NOT NULL REFERENCES matches (id) ON DELETE CASCADE,
  team_id                    BIGINT NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  side                       team_side NOT NULL,
  xg                         REAL,
  xga                        REAL,
  shots                      SMALLINT,
  sot                        SMALLINT,
  possession                 REAL,
  corners_for                SMALLINT,
  fouls                      SMALLINT,
  yellows                    SMALLINT,
  reds                       SMALLINT,
  ppda_proxy                 REAL,
  passes_into_box            SMALLINT,
  progressive_passes         SMALLINT,
  high_turnovers             SMALLINT,
  avg_def_line_height_proxy  REAL,
  tactical_profile_vector    JSONB NOT NULL DEFAULT '{}'::jsonb,
  source                     TEXT,
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (match_id, team_id)
);

CREATE TABLE players (
  id               BIGSERIAL PRIMARY KEY,
  team_id          BIGINT REFERENCES teams (id) ON DELETE SET NULL,
  display_name     TEXT NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE player_match_stats (
  id             BIGSERIAL PRIMARY KEY,
  match_id       BIGINT NOT NULL REFERENCES matches (id) ON DELETE CASCADE,
  team_id        BIGINT NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  player_id      BIGINT NOT NULL REFERENCES players (id) ON DELETE CASCADE,
  minutes        SMALLINT NOT NULL DEFAULT 0,
  xg_contrib     REAL,
  shots          SMALLINT,
  cards          SMALLINT,
  rating_proxy   REAL,
  UNIQUE (match_id, player_id)
);

CREATE TABLE match_events (
  id            BIGSERIAL PRIMARY KEY,
  match_id      BIGINT NOT NULL REFERENCES matches (id) ON DELETE CASCADE,
  minute        SMALLINT,
  event_type    TEXT NOT NULL,
  payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE standings_snapshots (
  id             BIGSERIAL PRIMARY KEY,
  season_id      BIGINT NOT NULL REFERENCES seasons (id) ON DELETE CASCADE,
  team_id        BIGINT NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  snapshot_at    TIMESTAMPTZ NOT NULL,
  matchweek      SMALLINT,
  rank           SMALLINT NOT NULL,
  points         SMALLINT NOT NULL,
  goals_for      SMALLINT,
  goals_against  SMALLINT,
  played         SMALLINT,
  title_prob_proxy REAL,
  source         TEXT,
  UNIQUE (season_id, team_id, snapshot_at)
);

CREATE TABLE match_context (
  match_id                  BIGINT PRIMARY KEY REFERENCES matches (id) ON DELETE CASCADE,
  derby_match_indicator     BOOLEAN NOT NULL DEFAULT FALSE,
  rivalry_score             REAL NOT NULL DEFAULT 0,
  revenge_match_indicator   BOOLEAN NOT NULL DEFAULT FALSE,
  big_match_indicator       BOOLEAN NOT NULL DEFAULT FALSE,
  travel_km_away_team       REAL,
  travel_km_home_team       REAL,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE injuries (
  id               BIGSERIAL PRIMARY KEY,
  player_id        BIGINT NOT NULL REFERENCES players (id) ON DELETE CASCADE,
  team_id          BIGINT NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  start_at         TIMESTAMPTZ NOT NULL,
  end_at           TIMESTAMPTZ,
  severity         SMALLINT,
  expected_return  DATE,
  status           TEXT NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE suspensions (
  id          BIGSERIAL PRIMARY KEY,
  player_id BIGINT NOT NULL REFERENCES players (id) ON DELETE CASCADE,
  team_id     BIGINT NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  from_at     TIMESTAMPTZ NOT NULL,
  to_at       TIMESTAMPTZ NOT NULL,
  reason      TEXT
);

CREATE TABLE player_importance_weights (
  player_id   BIGINT NOT NULL REFERENCES players (id) ON DELETE CASCADE,
  season_id   BIGINT NOT NULL REFERENCES seasons (id) ON DELETE CASCADE,
  weight      REAL NOT NULL,
  valid_from  TIMESTAMPTZ NOT NULL,
  valid_to    TIMESTAMPTZ,
  PRIMARY KEY (player_id, season_id, valid_from)
);

CREATE TABLE elo_rating_history (
  id          BIGSERIAL PRIMARY KEY,
  team_id     BIGINT NOT NULL REFERENCES teams (id) ON DELETE CASCADE,
  season_id   BIGINT REFERENCES seasons (id) ON DELETE SET NULL,
  rating      REAL NOT NULL,
  rating_at   TIMESTAMPTZ NOT NULL,
  reason      TEXT
);

CREATE INDEX idx_elo_team_time ON elo_rating_history (team_id, rating_at DESC);

CREATE TABLE feature_definitions (
  id             BIGSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  category       TEXT NOT NULL,
  description    TEXT,
  version        INT NOT NULL DEFAULT 1,
  dtype          TEXT NOT NULL,
  leakage_notes  TEXT,
  UNIQUE (name, version)
);

CREATE TABLE match_feature_sets (
  id                   BIGSERIAL PRIMARY KEY,
  match_id             BIGINT NOT NULL REFERENCES matches (id) ON DELETE CASCADE,
  pipeline_version     TEXT NOT NULL,
  computed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  feature_vector       JSONB NOT NULL,
  schema_hash          TEXT,
  is_training_eligible BOOLEAN NOT NULL DEFAULT TRUE,
  debug_trace          JSONB,
  UNIQUE (match_id, pipeline_version)
);

CREATE TABLE training_dataset_manifests (
  id             BIGSERIAL PRIMARY KEY,
  name           TEXT NOT NULL,
  sql_query_hash TEXT,
  row_count      BIGINT,
  min_kickoff    TIMESTAMPTZ,
  max_kickoff    TIMESTAMPTZ,
  label_version  TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE training_examples (
  id           BIGSERIAL PRIMARY KEY,
  manifest_id  BIGINT NOT NULL REFERENCES training_dataset_manifests (id) ON DELETE CASCADE,
  match_id     BIGINT NOT NULL REFERENCES matches (id) ON DELETE CASCADE,
  labels       JSONB NOT NULL,
  features     JSONB NOT NULL,
  split_tag    TEXT,
  UNIQUE (manifest_id, match_id)
);

CREATE TABLE ml_models (
  id           BIGSERIAL PRIMARY KEY,
  name         TEXT NOT NULL,
  framework    TEXT NOT NULL,
  artifact_uri TEXT,
  metrics      JSONB NOT NULL DEFAULT '{}'::jsonb,
  active       BOOLEAN NOT NULL DEFAULT FALSE,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE predictions (
  id                   BIGSERIAL PRIMARY KEY,
  match_id             BIGINT NOT NULL REFERENCES matches (id) ON DELETE CASCADE,
  model_id             BIGINT NOT NULL REFERENCES ml_models (id) ON DELETE RESTRICT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  probs                JSONB NOT NULL,
  extras               JSONB NOT NULL DEFAULT '{}'::jsonb,
  calibration_version  TEXT
);

CREATE TABLE prediction_explanations (
  id                 BIGSERIAL PRIMARY KEY,
  prediction_id      BIGINT NOT NULL REFERENCES predictions (id) ON DELETE CASCADE,
  llm_model          TEXT NOT NULL,
  structured_facts   JSONB NOT NULL,
  explanation_text   TEXT,
  safety_flags       JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;

CREATE INDEX idx_matches_kickoff ON matches (kickoff_at);
CREATE INDEX idx_matches_season_kickoff ON matches (season_id, kickoff_at);
CREATE INDEX idx_matches_home_kickoff ON matches (home_team_id, kickoff_at);
CREATE INDEX idx_matches_away_kickoff ON matches (away_team_id, kickoff_at);
CREATE INDEX idx_matches_status ON matches (status);

CREATE INDEX idx_tms_team_match ON team_match_stats (team_id, match_id);
CREATE INDEX idx_tms_match ON team_match_stats (match_id);

CREATE INDEX idx_pms_match ON player_match_stats (match_id);
CREATE INDEX idx_pms_team ON player_match_stats (team_id);

CREATE INDEX idx_standings_season_snap ON standings_snapshots (season_id, snapshot_at);
CREATE INDEX idx_standings_team_snap ON standings_snapshots (team_id, snapshot_at);

CREATE INDEX idx_match_feature_sets_computed ON match_feature_sets (computed_at DESC);
CREATE INDEX idx_predictions_match_created ON predictions (match_id, created_at DESC);
CREATE INDEX idx_predictions_model ON predictions (model_id);

CREATE INDEX idx_injuries_player_start ON injuries (player_id, start_at);
CREATE INDEX idx_suspensions_player_from ON suspensions (player_id, from_at);

-- =============================================================================
-- NEXT STEPS (recommended)
-- =============================================================================
-- 1. Mirror these tables in SQLAlchemy models and add Alembic for migrations.
-- 2. Ingest one league season: leagues -> seasons -> teams -> matches ->
--    team_match_stats.
-- 3. Document feature_lock_at (e.g. T-60m); use the same rule in training and
--    inference for injuries and lineups.
-- 4. Implement first feature job: rolling last-5 form -> match_feature_sets
--    as JSON with a pipeline_version string.
-- 5. Export training rows (Parquet) from a time-bounded query joining finished
--    matches + labels + feature snapshots; use time-based train/val/test.
-- 6. When tables grow large, add table partitioning on matches.kickoff_at and
--    partial indexes (e.g. WHERE status = 'finished') for analytics queries.
-- =============================================================================
