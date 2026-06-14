from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import League


def list_all(db: Session) -> list[League]:
    stmt = select(League).order_by(League.name)
    return list(db.scalars(stmt).all())


def get_by_id(db: Session, league_id: int) -> League | None:
    return db.get(League, league_id)


def get_by_code(db: Session, code: str) -> League | None:
    return db.scalars(select(League).where(League.code == code)).first()
