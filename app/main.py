"""Football AI API entrypoint. Importing config first loads `.env` into the process."""
import logging

from app.core import config as _config  # noqa: F401 — side effect: load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.routes.health import router as health_router
from app.routes.leagues import router as leagues_router
from app.routes.matches import router as matches_router
from app.routes.prediction import router as prediction_router
from app.routes.seasons import router as seasons_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("football_ai")

app = FastAPI(
    title="Football AI API",
    description="Fixtures and baseline match predictions from PostgreSQL.",
    version="0.2.0",
)

app.include_router(health_router)
app.include_router(leagues_router)
app.include_router(seasons_router)
app.include_router(matches_router)
app.include_router(prediction_router)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/")
def home():
    return {"message": "Football AI Backend Running"}
