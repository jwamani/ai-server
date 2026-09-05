"""Password hashing and JWT token operations."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from src.config.settings import Settings

_password_hash = PasswordHash.recommended()


class InvalidAccessTokenError(ValueError):
    """Raised when an access token cannot be authenticated."""


def hash_password(password: str) -> str:
    """Hash a password using the current recommended Argon2 configuration."""

    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a password matches its stored hash."""

    return _password_hash.verify(password, password_hash)


def create_access_token(user_id: UUID, settings: Settings) -> str:
    """Create a short-lived signed access token for one user."""

    if settings.jwt_secret is None:
        raise RuntimeError("JWT_SECRET must be set before issuing access tokens.")
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": str(user_id), "exp": expires_at, "type": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> UUID:
    """Validate an access token and return its authenticated user identifier."""

    if settings.jwt_secret is None:
        raise RuntimeError("JWT_SECRET must be set before validating access tokens.")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not isinstance(subject, str) or token_type != "access":
            raise InvalidAccessTokenError("Invalid access token claims.")
        return UUID(subject)
    except (jwt.InvalidTokenError, ValueError) as error:
        if isinstance(error, InvalidAccessTokenError):
            raise
        raise InvalidAccessTokenError("Invalid or expired access token.") from error
