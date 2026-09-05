"""Local user registration and authentication endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.api.dependencies import SessionDependency, SettingsDependency
from src.api.schemas import AccessTokenResponse, LoginRequest, RegisterUserRequest, UserResponse
from src.infrastructure.database.models import User
from src.infrastructure.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterUserRequest, session: SessionDependency) -> UserResponse:
    """Register a local user with an Argon2 password hash."""

    user = User(
        email=payload.email.lower(),
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email address.",
        ) from error
    session.refresh(user)
    return UserResponse(id=user.id, email=user.email, name=user.name)


@router.post("/login", response_model=AccessTokenResponse)
def login(
    payload: LoginRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> AccessTokenResponse:
    """Authenticate a user and return a signed bearer token."""

    user = session.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive."
        )
    return AccessTokenResponse(access_token=create_access_token(user.id, settings=settings))
