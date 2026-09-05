"""Shared FastAPI dependencies."""

from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import Settings, get_settings
from src.infrastructure.database.models import User
from src.infrastructure.database.session import create_session_factory
from src.infrastructure.security import InvalidAccessTokenError, decode_access_token


def get_session(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Generator[Session, None, None]:
    """Provide a transaction-scoped database session to one request."""

    if settings.database_url is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured.",
        )
    session_factory = create_session_factory(settings.database_url)
    with session_factory() as session:
        yield session


SessionDependency = Annotated[Session, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]

_bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)]


def get_current_user(
    credentials: BearerCredentials,
    session: SessionDependency,
    settings: SettingsDependency,
) -> User:
    """Authenticate an active user from a bearer token."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id: UUID = decode_access_token(credentials.credentials, settings)
    except (InvalidAccessTokenError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    user = session.scalar(select(User).where(User.id == user_id))
    if user is None or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token."
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
