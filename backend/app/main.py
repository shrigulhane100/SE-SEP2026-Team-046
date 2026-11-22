from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.auth import admin_router, auth_router
from app.config import Settings
from app.db import create_db_engine, get_session
from app.guidance import admin_guidance_router, guidance_router
from app.mentors import mentor_router, student_mentor_router, verification_router
from app.profiles import profile_router
from app.schemas import ErrorResponse, HealthResponse

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(profile_router)
router.include_router(guidance_router)
router.include_router(admin_guidance_router)
router.include_router(mentor_router)
router.include_router(student_mentor_router)
router.include_router(verification_router)


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
    app.state.settings = settings

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, exc: RequestValidationError) -> JSONResponse:
        # Validation errors can otherwise echo submitted passwords or the entire body.
        details = [
            {key: error[key] for key in ("loc", "msg", "type")}
            for error in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": details})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(router)
    return app
