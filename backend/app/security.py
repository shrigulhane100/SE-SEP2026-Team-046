from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import AuthSession, User

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "rockstarz"
JWT_AUDIENCE = "rockstarz-api"

password_hasher = PasswordHash.recommended()
dummy_password_hash = password_hasher.hash(token_urlsafe(32))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        verified = password_hasher.verify(
            password, password_hash or dummy_password_hash
        )
    except UnknownHashError:
        return False
    return password_hash is not None and verified


def issue_access_token(db: Session, user: User, settings: Settings) -> str:
    now = datetime.now(UTC).replace(microsecond=0)
    expires_at = now + timedelta(minutes=settings.jwt_expiry_minutes)
    session_id = uuid4()
    db.execute(
        delete(AuthSession).where(
            AuthSession.user_id == user.user_id, AuthSession.expires_at <= now
        )
    )
    db.add(
        AuthSession(session_id=session_id, user_id=user.user_id, expires_at=expires_at)
    )
    return jwt.encode(
        {
            "sub": str(user.user_id),
            "jti": str(session_id),
            "iat": now,
            "exp": expires_at,
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str, settings: Settings) -> tuple[str, UUID]:
    claims = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["sub", "jti", "iat", "exp", "iss", "aud"]},
    )
    return claims["sub"], UUID(claims["jti"])
