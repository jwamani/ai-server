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


class CreateRepositoryRequest(BaseModel):
    """Input required to register a repository."""

    provider: str = Field(default="git", min_length=1, max_length=64)
    remote_url: str = Field(min_length=1, max_length=2048)
    default_branch: str = Field(default="main", min_length=1, max_length=255)
    visibility: str = Field(default="private", min_length=1, max_length=32)


class RepositoryResponse(BaseModel):
    """Public repository representation."""

    id: UUID
    project_id: UUID
    provider: str
    remote_url: str
    default_branch: str
    visibility: str


class CreateTaskRequest(BaseModel):
    """Input required to create a coding task."""

    repository_id: UUID
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(min_length=1, max_length=10_000)
    base_branch: str = Field(default="main", min_length=1, max_length=255)
    max_iterations: int = Field(default=20, ge=1, le=100)
    timeout_seconds: int = Field(default=3600, ge=60, le=86400)


class TaskResponse(BaseModel):
    """Public task representation."""

    id: UUID
    project_id: UUID
    repository_id: UUID
    created_by_id: UUID
    trace_id: UUID
    title: str
    description: str
    status: str
    base_branch: str
    agent_branch: str | None
    max_iterations: int
    timeout_seconds: int
    started_at: str | None
    completed_at: str | None
