"""Baseline 1X2 prediction from rolling goals form (stored or computed)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MLModel, Match, Prediction, Team, TeamMatchStat
from app.services import match_service

ACTIVE_MODEL_NAME = "baseline_form_v1"


def _team_strength(db: Session, team_id: int, before: datetime) -> float:
    """Avg (goals_for - goals_against) from finished team_match_stats before kickoff."""
    stmt = (
        select(TeamMatchStat)
        .join(Match, TeamMatchStat.match_id == Match.id)
        .where(
            TeamMatchStat.team_id == team_id,
            Match.status == "finished",
            Match.kickoff_at < before,
        )
        .order_by(Match.kickoff_at.desc())
        .limit(5)
    )
    stats = list(db.scalars(stmt).all())
    if not stats:
        return 0.0
    total = 0.0
    for s in stats:
        m = db.get(Match, s.match_id)
        if m is None:
            continue
        if s.team_id == m.home_team_id:
            gf, ga = m.home_score or 0, m.away_score or 0
        else:
            gf, ga = m.away_score or 0, m.home_score or 0
        total += gf - ga
    return total / len(stats)


def _probs_from_strength(home_s: float, away_s: float) -> tuple[float, float, float]:
    """Map strength diff to home/draw/away percentages (simple logistic-style)."""
    diff = home_s - away_s
    home_raw = 1.0 / (1.0 + pow(2.718, -diff * 0.35))
    away_raw = 1.0 / (1.0 + pow(2.718, diff * 0.35))
    draw_raw = 0.28
    total = home_raw + draw_raw + away_raw
    home_pct = round(home_raw / total * 100, 1)
    draw_pct = round(draw_raw / total * 100, 1)
    away_pct = round(100.0 - home_pct - draw_pct, 1)
    return home_pct, draw_pct, away_pct


def _get_or_create_active_model(db: Session) -> MLModel:
    model = db.scalars(
        select(MLModel).where(MLModel.name == ACTIVE_MODEL_NAME)
    ).first()
    if model:
        return model
    model = MLModel(
        name=ACTIVE_MODEL_NAME,
        framework="baseline",
        active=True,
        metrics={"type": "rolling_goals_form"},
    )
    db.add(model)
    db.flush()
    return model


def compute_prediction(db: Session, match_id: int) -> dict:
    row = match_service.get_match(db, match_id)
    if row is None:
        raise ValueError("match_not_found")

    model = _get_or_create_active_model(db)
    existing = db.scalars(
        select(Prediction)
        .where(Prediction.match_id == match_id, Prediction.model_id == model.id)
        .order_by(Prediction.created_at.desc())
    ).first()

    if existing and existing.probs:
        p = existing.probs
        return {
            "match_id": match_id,
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "home_win": float(p.get("home_win", 0)),
            "draw": float(p.get("draw", 0)),
            "away_win": float(p.get("away_win", 0)),
            "model_name": model.name,
            "source": "stored",
            "notes": "Loaded from predictions table",
        }

    kickoff = row["kickoff_at"]
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=timezone.utc)

    home_s = _team_strength(db, row["home_team_id"], kickoff) + 0.15  # small home advantage
    away_s = _team_strength(db, row["away_team_id"], kickoff)
    home_pct, draw_pct, away_pct = _probs_from_strength(home_s, away_s)

    probs = {"home_win": home_pct, "draw": draw_pct, "away_win": away_pct}
    pred = Prediction(
        match_id=match_id,
        model_id=model.id,
        probs=probs,
        extras={"home_strength": home_s, "away_strength": away_s},
    )
    db.add(pred)
    db.commit()

    return {
        "match_id": match_id,
        "home_team": row["home_team"],
        "away_team": row["away_team"],
        "home_win": home_pct,
        "draw": draw_pct,
        "away_win": away_pct,
        "model_name": model.name,
        "source": "computed",
        "notes": "Baseline from last-5 goal difference + home boost",
    }
