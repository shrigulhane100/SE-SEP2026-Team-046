from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_session
from app.main import create_app
from app.models import AuthSession, StudentProfile, User, UserRole
from app.security import (
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    decode_access_token,
    hash_password,
    issue_access_token,
    verify_password,
)

PASSWORD = "a-long-test-password"
EMAIL = "student@example.com"


@pytest.fixture
def settings():
    return Settings(
        database_url="postgresql+psycopg://localhost/rockstarz_test",
        jwt_secret="local-test-signing-key-for-auth-tests",
    )


@pytest.fixture
def student():
    return User(
        user_id=42,
        name="Test Student",
        email=EMAIL,
        role=UserRole.STUDENT,
        password_hash=hash_password(PASSWORD),
        is_active=True,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def client_and_db(settings):
    app = create_app(settings)
    db = Mock(spec=Session)
    app.dependency_overrides[get_session] = lambda: db
    with TestClient(app) as client:
        yield client, db


def test_argon2_password_hash_verifies_the_password(student):
    assert student.password_hash.startswith("$argon2id$")
    assert verify_password(PASSWORD, student.password_hash)
    assert not verify_password("incorrect", student.password_hash)
    assert not verify_password(PASSWORD, None)


def test_expired_jwt_is_rejected(settings):
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "42",
            "jti": str(uuid4()),
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, settings)


def test_register_creates_the_student_and_profile_in_one_transaction(client_and_db):
    client, db = client_and_db
    db.scalar.return_value = None

    def assign_database_defaults():
        user = db.add.call_args.args[0]
        user.user_id = 42
        user.is_active = True
        user.created_at = datetime.now(UTC)

    db.flush.side_effect = assign_database_defaults
    response = client.post(
        "/api/v1/auth/register",
        json={
            "role": "STUDENT",
            "name": "Test Student",
            "email": EMAIL.upper(),
            "password": PASSWORD,
            "roll_number": "24f2000001",
            "career_objective": "PLACEMENT",
        },
    )

    assert response.status_code == 201
    assert response.json()["user"]["email"] == EMAIL
    assert "password_hash" not in response.json()["user"]
    user, profile, session = [call.args[0] for call in db.add.call_args_list]
    assert verify_password(PASSWORD, user.password_hash)
    assert isinstance(profile, StudentProfile)
    assert (profile.user_id, profile.roll_number, profile.career_objective) == (
        user.user_id,
        "24F2000001",
        "PLACEMENT",
    )
    assert isinstance(session, AuthSession)
    db.commit.assert_called_once()


def test_public_registration_rejects_an_admin(client_and_db):
    client, db = client_and_db

    response = client.post(
        "/api/v1/auth/register",
        json={
            "role": "ADMIN",
            "name": "Test Admin",
            "email": EMAIL,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 403
    db.add.assert_not_called()


def test_registration_validation_does_not_echo_the_password(client_and_db):
    client, _ = client_and_db

    response = client.post(
        "/api/v1/auth/register",
        json={
            "role": "STUDENT",
            "name": "Test Student",
            "email": EMAIL,
            "password": PASSWORD,
        },
    )

    assert response.status_code == 422
    assert "A student roll number is required" in response.json()["detail"][0]["msg"]
    assert PASSWORD not in response.text


def test_login_issues_a_token_with_the_frontend_user_shape(
    client_and_db, student, settings
):
    client, db = client_and_db
    db.scalar.return_value = student

    response = client.post(
        "/api/v1/auth/login", json={"email": EMAIL.upper(), "password": PASSWORD}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["id"] == student.user_id
    assert payload["user"]["role"] == "STUDENT"
    subject, session_id = decode_access_token(payload["access_token"], settings)
    assert subject == str(student.user_id)
    assert session_id == db.add.call_args.args[0].session_id


def test_invalid_credentials_return_a_generic_401(client_and_db, student):
    client, db = client_and_db
    db.scalar.return_value = student

    wrong_password = client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": "wrong-password"}
    )
    db.scalar.return_value = None
    unknown_email = client.post(
        "/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert (
        wrong_password.json()
        == unknown_email.json()
        == {"detail": "Incorrect email or password"}
    )
    db.commit.assert_not_called()


def test_protected_endpoint_requires_a_bearer_token(client_and_db):
    client, _ = client_and_db
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_student_cannot_read_the_admin_user_list(client_and_db, student, settings):
    client, db = client_and_db
    token = issue_access_token(db, student, settings)
    db.execute.return_value.one_or_none.return_value = SimpleNamespace(
        User=student, AuthSession=db.add.call_args.args[0]
    )

    response = client.get(
        "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403


def test_logout_revokes_the_token(client_and_db, student, settings):
    client, db = client_and_db
    token = issue_access_token(db, student, settings)
    session = db.add.call_args.args[0]
    db.execute.return_value.one_or_none.side_effect = (
        SimpleNamespace(User=student, AuthSession=session),
        None,
    )
    headers = {"Authorization": f"Bearer {token}"}

    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    db.delete.assert_called_once_with(session)
    db.commit.assert_called_once()
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
