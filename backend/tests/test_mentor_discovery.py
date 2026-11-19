from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import Settings
from app.db import get_session
from app.main import create_app
from app.models import GuidanceArea, MentorProfile, MentorVerification, User, UserRole


@pytest.fixture
def discovery():
    app = create_app(
        Settings(
            database_url="postgresql+psycopg://localhost/rockstarz_test",
            jwt_secret="local-test-signing-key-for-mentor-discovery",
        )
    )
    db = Mock(spec=Session)
    user = User(user_id=1, role=UserRole.STUDENT)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as client:
        yield client, db, user


@pytest.fixture
def mentor():
    return MentorProfile(
        profile_id=50,
        user_id=9,
        mentor_type="Faculty",
        industry="Education",
        experience_years=6,
        max_mentees=3,
        is_accepting=True,
        verification_status=MentorVerification.VERIFIED,
        guidance_areas=[
            GuidanceArea(area_id=30, name="Inactive area", is_active=False),
            GuidanceArea(area_id=20, name="Research", is_active=True),
            GuidanceArea(area_id=10, name="Placements", is_active=True),
        ],
    )


def test_student_list_returns_a_match_score_and_public_fields(discovery, mentor):
    client, db, _ = discovery
    db.scalars.return_value = [10, 20, 40]
    db.execute.return_value = [(mentor, "Mentor Name", 2, 0)]

    response = client.get("/api/v1/mentors")
    assert response.status_code == 200
    result = response.json()[0]
    assert result["id"] == 9
    assert result["area_ids"] == [10, 20]
    assert result["areas"] == ["Placements", "Research"]
    assert result["match"] == 67
    assert result["available"] is True
    assert "email" not in result


def test_public_discovery_returns_null_match_for_an_unavailable_mentor(
    discovery, mentor
):
    client, db, _ = discovery
    mentor.is_accepting = False
    db.execute.return_value = [(mentor, "Mentor Name", 0, 0)]

    response = client.get("/api/v1/public/mentors?limit=3&offset=1")
    assert response.status_code == 200
    result = response.json()[0]
    assert result["match"] is None
    assert result["available"] is False


def test_student_get_returns_not_found_for_a_hidden_mentor(discovery):
    client, db, _ = discovery
    db.scalars.return_value = []
    db.execute.return_value.one_or_none.return_value = None

    response = client.get("/api/v1/mentors/9")
    assert response.status_code == 404
    assert response.json() == {"detail": "Mentor not found"}


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
        "min_experience=-1",
        "area_id=no",
        "availability=other",
        "sort=other",
        "unknown=value",
    ],
)
def test_invalid_filters_are_rejected_before_querying(discovery, query):
    client, db, _ = discovery

    assert client.get(f"/api/v1/mentors?{query}").status_code == 422
    db.execute.assert_not_called()


def test_mentor_account_cannot_use_student_discovery(discovery):
    client, db, user = discovery
    user.role = UserRole.MENTOR

    assert client.get("/api/v1/mentors").status_code == 403
    db.execute.assert_not_called()


def test_student_cannot_approve_a_mentor(discovery):
    client, db, _ = discovery

    response = client.post("/api/v1/admin/mentors/9/verify", json={"approve": True})
    assert response.status_code == 403
    db.commit.assert_not_called()


def test_administrator_can_list_and_revoke_verification(discovery, mentor):
    client, db, user = discovery
    user.role = UserRole.ADMIN
    db.execute.return_value = [
        (mentor, "Mentor Name", "mentor@example.com", datetime.now(UTC), True, 0)
    ]
    db.scalar.return_value = mentor

    result = client.get("/api/v1/admin/mentor-verifications")
    assert result.status_code == 200
    assert result.json()[0]["email"] == "mentor@example.com"

    decision = client.post("/api/v1/admin/mentors/9/verify", json={"approve": False})
    assert decision.status_code == 200
    assert decision.json() == {"ok": True}
    assert mentor.verification_status == MentorVerification.REJECTED
    db.commit.assert_called_once()
