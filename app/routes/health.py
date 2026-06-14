from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_database_url
from app.db.session import get_db
from app.schemas.common import DbHealthOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/db", response_model=DbHealthOut)
def health_db(db: Session = Depends(get_db)):
    count = db.execute(
        text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'")
    ).scalar()
    return DbHealthOut(
        status="ok",
        database=get_database_url().split("/")[-1],
        public_table_count=int(count or 0),
    )
