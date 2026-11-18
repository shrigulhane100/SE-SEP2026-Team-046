from contextlib import nullcontext
from datetime import UTC, datetime
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
    MentorProfile,
    MentorVerification,
    StudentProfile,
    User,
    UserRole,
)


@pytest.fixture
def api():
    settings = Settings(
        database_url="postgresql+psycopg://localhost/rockstarz_test",
        jwt_secret="local-test-signing-key-for-profile-tests",
    )
    app = create_app(settings)
    db = Mock(spec=Session)
    db.no_autoflush = nullcontext()
    user = User(
        user_id=7,
        name="Account Owner",
        email="owner@example.com",
        role=UserRole.STUDENT,
        is_active=True,
        created_at=datetime.now(UTC),
    )
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as client:
        yield client, db, user


def test_student_profile_uses_the_frontend_field_names(api):
    client, db, _ = api
    db.scalar.return_value = StudentProfile(
        profile_id=22,
        user_id=7,
        roll_number="STUDENT1",
        level="Degree",
        skills=["Python"],
        guidance_areas=[GuidanceArea(area_id=3, name="Software Engineering")],
    )

    response = client.get("/api/v1/profile/me")

    assert response.status_code == 200
    assert response.json()["profile"]["id"] == 22
    assert response.json()["profile"]["academic_level"] == "Degree"
    assert response.json()["profile"]["skills"] == ["Python"]
    assert response.json()["area_ids"] == [3]


def test_mentor_save_retains_omitted_fields_and_replaces_mappings(api):
    client, db, user = api
    user.role = UserRole.MENTOR
    profile = MentorProfile(
        profile_id=22,
        user_id=7,
        experience_years=4,
        max_mentees=3,
        is_accepting=True,
        verification_status=MentorVerification.PENDING,
        guidance_areas=[GuidanceArea(area_id=1, name="Data Science")],
    )
    db.scalar.side_effect = [user, profile]
    area = GuidanceArea(area_id=2, name="Software Engineering", is_active=True)
    db.scalars.return_value = [area]

    response = client.put(
        "/api/v1/profile/me",
        json={
            "education": "MS in Computer Science",
            "past_roles": ["Engineer"],
            "is_accepting": False,
            "area_ids": [2],
        },
    )

    assert response.status_code == 200
    assert response.json()["profile"]["education"] == "MS in Computer Science"
    assert response.json()["profile"]["past_roles"] == ["Engineer"]
    assert profile.experience_years == 4
    assert profile.is_accepting is False
    assert response.json()["area_ids"] == [2]
    assert profile.guidance_areas == [area]
    db.commit.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        {"area_ids": [1, 1]},
        {"area_ids": [0]},
        {"area_ids": ["1"]},
        {"max_mentees": 3},
        {"role": "ADMIN"},
        {"name": None},
    ],
)
def test_profile_update_rejects_invalid_or_wrong_role_fields(api, payload):
    client, db, _ = api

    response = client.put("/api/v1/profile/me", json=payload)

    assert response.status_code == 422
    db.commit.assert_not_called()


def test_inactive_area_cannot_be_added_to_a_profile(api):
    client, db, user = api
    profile = StudentProfile(
        profile_id=22, user_id=7, roll_number="STUDENT1", guidance_areas=[]
    )
    db.scalar.side_effect = [user, profile]
    db.scalars.return_value = [
        GuidanceArea(area_id=12, name="Inactive area", is_active=False)
    ]

    response = client.put("/api/v1/profile/me", json={"area_ids": [12]})

    assert response.status_code == 422
    assert response.json() == {"detail": "Inactive guidance areas cannot be selected"}
    assert profile.guidance_areas == []
    db.commit.assert_not_called()


def test_guidance_admin_routes_require_administrator(api):
    client, db, _ = api

    response = client.post(
        "/api/v1/admin/guidance-areas", json={"name": "Career exploration"}
    )

    assert response.status_code == 403
    db.add.assert_not_called()


def test_guidance_admin_can_deactivate_an_area(api):
    client, db, user = api
    user.role = UserRole.ADMIN
    area = GuidanceArea(area_id=3, name="Career exploration", is_active=True)
    db.get.return_value = area

    response = client.patch("/api/v1/admin/guidance-areas/3", json={"is_active": False})

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert area.is_active is False
    db.commit.assert_called_once()
