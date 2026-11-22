from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.db import create_db_engine, get_session
from app.schemas import ErrorResponse, HealthResponse

router = APIRouter(prefix="/api/v1")


@router.get(
    "/health",
    tags=["Health"],
    responses={
        503: {"model": ErrorResponse, "description": "PostgreSQL is unavailable"},
    },
)
def health_check(session: Annotated[Session, Depends(get_session)]) -> HealthResponse:
    """Check whether the API can execute a query against PostgreSQL."""
    try:
        session.execute(text("SELECT 1"))
    except OperationalError:
        raise HTTPException(status_code=503, detail="Database unavailable") from None
    return HealthResponse(status="ok", database="reachable")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings)
        app.state.session_factory = sessionmaker(bind=engine)
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Rock Starz API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(router)
    return app
