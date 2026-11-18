from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_session
from app.main import create_app


@pytest.fixture
def client_and_session():
    app = create_app(
        Settings(
            database_url="postgresql+psycopg://localhost/rockstarz_test",
            cors_origins=["http://localhost:5173"],
        )
    )
    session = Mock(spec=Session)
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as client:
        yield client, session


def test_health_checks_the_database(client_and_session):
    client, session = client_and_session

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}
    session.execute.assert_called_once()
    assert str(session.execute.call_args.args[0]) == "SELECT 1"


def test_health_reports_a_database_failure_without_connection_details(
    client_and_session,
):
    client, session = client_and_session
    session.execute.side_effect = OperationalError(
        "SELECT 1", {}, RuntimeError("private connection details")
    )

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_cors_allows_the_configured_frontend_origin(client_and_session):
    client, _ = client_and_session

    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
