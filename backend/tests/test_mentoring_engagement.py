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
    Goal,
    GoalStatus,
    GuidanceArea,
    MentoringRelationship,
    MentoringRequest,
    MentoringType,
    Notification,
    NotificationReference,
    NotificationType,
    RelationshipStatus,
    User,
    UserRole,
)


@pytest.fixture
def api():
    app = create_app(
        Settings(
            database_url="postgresql+psycopg://localhost/rockstarz_test",
            jwt_secret="local-test-signing-key-for-engagement-tests",
        )
    )
    db = Mock(spec=Session)
    student = User(user_id=1, name="Student", role=UserRole.STUDENT)
    app.dependency_overrides[get_current_user] = lambda: student
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as client:
        yield client, db, student


@pytest.fixture
def relationship(api):
    _, _, student = api
    now = datetime.now(UTC)
    request = MentoringRequest(
        request_id=7,
        student_id=1,
        mentor_id=2,
        area_id=3,
        student=student,
        mentor=User(user_id=2, name="Mentor", role=UserRole.MENTOR),
        area=GuidanceArea(area_id=3, name="Placements"),
        type=MentoringType.LONG_TERM,
    )
    return MentoringRelationship(
        relationship_id=10,
        request_id=7,
        request=request,
        status=RelationshipStatus.ACTIVE,
        started_at=now,
    )


def test_updating_goal_recalculates_relationship_progress(api, relationship):
    client, db, student = api
    db.scalar.side_effect = [10, relationship]
    relationship.goals = [
        Goal(
            goal_id=8,
            relationship_id=10,
            author=student,
            created_by=1,
            title="Practice interviews",
            status=GoalStatus.TODO,
            created_at=relationship.started_at,
        )
    ]

    response = client.patch("/api/v1/goals/8", json={"status": "DONE"})

    assert response.status_code == 200
    assert response.json()["goals"][0]["status"] == "DONE"
    assert response.json()["goals"][0]["created_by_name"] == "Student"
    assert response.json()["progress"] == 100
    db.commit.assert_called_once()


def test_goal_cannot_be_created_on_completed_relationship(api, relationship):
    client, db, _ = api
    relationship.status = RelationshipStatus.COMPLETED
    db.scalar.return_value = relationship

    assert (
        client.post(
            "/api/v1/relationships/10/goals", json={"title": "New goal"}
        ).status_code
        == 409
    )
    db.add.assert_not_called()


def test_activity_rejects_a_future_date(api):
    client, db, _ = api
    tomorrow = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()

    response = client.post(
        "/api/v1/relationships/10/activities",
        json={
            "activity_type": "MEETING",
            "notes": "Discussed the interview",
            "activity_date": tomorrow,
        },
    )

    assert response.status_code == 422
    db.add.assert_not_called()


@pytest.mark.parametrize("rating", [0, 6, 3.5, "5", True])
def test_rating_must_be_an_integer_from_one_to_five(api, rating):
    client, db, _ = api
    assert (
        client.post(
            "/api/v1/relationships/10/feedback", json={"rating": rating}
        ).status_code
        == 422
    )
    db.add.assert_not_called()


def test_feedback_requires_relationship_membership(api):
    client, db, _ = api
    db.scalar.return_value = None
    assert (
        client.post("/api/v1/relationships/10/feedback", json={"rating": 5}).status_code
        == 404
    )
    db.add.assert_not_called()


def test_notification_list_reports_unread_count(api):
    client, db, _ = api
    db.scalars.return_value = [
        Notification(
            notification_id=index,
            user_id=1,
            type=NotificationType.REQUEST_ACCEPTED,
            message="Your request was accepted.",
            reference_type=NotificationReference.RELATIONSHIP,
            reference_id=10,
            is_read=is_read,
            created_at=datetime.now(UTC),
        )
        for index, is_read in ((1, False), (2, True))
    ]
    response = client.get("/api/v1/notifications")
    assert response.status_code == 200
    assert response.json()["unread"] == 1
    assert response.json()["items"][0]["reference_id"] == 10


def test_marking_an_unowned_notification_returns_not_found(api):
    client, db, _ = api
    db.scalar.return_value = None
    assert client.post("/api/v1/notifications/3/read").status_code == 404
    db.commit.assert_not_called()
