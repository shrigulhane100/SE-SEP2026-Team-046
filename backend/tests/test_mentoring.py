from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import Settings
from app.db import get_session
from app.main import create_app
from app.models import (
    GuidanceArea,
    MentoringRelationship,
    MentoringRequest,
    MentoringType,
    RelationshipStatus,
    RequestStatus,
    User,
    UserRole,
)


@pytest.fixture
def api():
    app = create_app(
        Settings(
            database_url="postgresql+psycopg://localhost/rockstarz_test",
            jwt_secret="local-test-signing-key-for-mentoring-tests",
        )
    )
    db = Mock(spec=Session)
    user = User(user_id=1, name="Student", role=UserRole.STUDENT)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as client:
        yield client, db, user


@pytest.fixture
def request_record(api):
    _, _, student = api
    now = datetime.now(UTC)
    return MentoringRequest(
        request_id=7,
        student_id=1,
        mentor_id=2,
        area_id=3,
        student=student,
        mentor=User(user_id=2, name="Mentor", role=UserRole.MENTOR),
        area=GuidanceArea(area_id=3, name="Placements"),
        message="I would like advice on preparing for interviews.",
        objective="",
        type=MentoringType.LONG_TERM,
        status=RequestStatus.PENDING,
        created_at=now,
        expires_at=now + timedelta(hours=48),
    )


def test_request_validates_message_and_type(api):
    client, db, _ = api
    response = client.post(
        "/api/v1/requests",
        json={
            "mentor_id": 2,
            "area_id": 3,
            "message": "Short",
            "type": "INVALID",
        },
    )
    assert response.status_code == 422
    db.add.assert_not_called()


def test_student_cannot_reject_a_request(api):
    client, db, _ = api
    assert client.post("/api/v1/requests/7/reject").status_code == 403
    db.commit.assert_not_called()


def test_student_can_cancel_their_pending_request(api, request_record):
    client, db, _ = api
    db.scalar.return_value = request_record
    response = client.post("/api/v1/requests/7/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    db.commit.assert_called_once()


def test_past_due_request_cannot_be_rejected(api, request_record):
    client, db, user = api
    user.role = UserRole.MENTOR
    request_record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.scalar.return_value = request_record
    db.scalars.return_value = [request_record]
    response = client.post("/api/v1/requests/7/reject")
    assert response.status_code == 409
    assert response.json()["detail"] == "Request is already expired"
    db.commit.assert_called_once()


def test_completed_relationship_cannot_be_reopened(api, request_record):
    client, db, _ = api
    db.scalar.return_value = MentoringRelationship(
        relationship_id=10,
        request_id=7,
        request=request_record,
        status=RelationshipStatus.COMPLETED,
        started_at=request_record.created_at,
    )
    response = client.patch(
        "/api/v1/relationships/10/status", json={"status": "ACTIVE"}
    )
    assert response.status_code == 409
    db.commit.assert_not_called()


def test_student_cannot_close_relationship(api, request_record):
    client, db, _ = api
    db.scalar.return_value = MentoringRelationship(
        relationship_id=10,
        request_id=7,
        request=request_record,
        status=RelationshipStatus.ACTIVE,
        started_at=request_record.created_at,
    )
    response = client.patch(
        "/api/v1/relationships/10/status", json={"status": "CLOSED"}
    )
    assert response.status_code == 403
    db.commit.assert_not_called()
