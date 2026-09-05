"""Request and response contracts for the HTTP API."""

from uuid import UUID

from pydantic import BaseModel, Field


class RegisterUserRequest(BaseModel):
    """Input required to create a locally authenticated user."""

    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    """Credentials for a local authentication attempt."""

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Public user representation."""

    id: UUID
    email: str
    name: str


class AccessTokenResponse(BaseModel):
    """Bearer token issued after successful authentication."""

    access_token: str
    token_type: str = "bearer"


class CreateProjectRequest(BaseModel):
    """Input required to create a project."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10_000)
    default_branch: str = Field(default="main", min_length=1, max_length=255)


class ProjectResponse(BaseModel):
    """Public project representation."""

    id: UUID
    name: str
    description: str | None
    default_branch: str
