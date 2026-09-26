"""ORM models for identity, projects, repositories, tasks, and execution records."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.project import ProjectRole
from src.domain.task import TaskStatus
from src.infrastructure.database.base import TimestampedModel


class User(TimestampedModel):
    """An authenticated platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="active")

    owned_projects: Mapped[list[Project]] = relationship(back_populates="owner")
    project_memberships: Mapped[list[ProjectMember]] = relationship(
        back_populates="user"
    )
    created_tasks: Mapped[list[Task]] = relationship(back_populates="created_by")


class Project(TimestampedModel):
    """A logical software project owned by a user."""

    __tablename__ = "projects"

    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")

    owner: Mapped[User] = relationship(back_populates="owned_projects")
    members: Mapped[list[ProjectMember]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    repositories: Mapped[list[Repository]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list[Task]] = relationship(back_populates="project")


class ProjectMember(TimestampedModel):
    """A user's role within a project."""

    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "user_id"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_role"),
        default=ProjectRole.DEVELOPER,
    )

    project: Mapped[Project] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="project_memberships")


class Repository(TimestampedModel):
    """A registered Git repository associated with one project."""

    __tablename__ = "repositories"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64), default="git")
    remote_url: Mapped[str] = mapped_column(String(2048), unique=True)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    visibility: Mapped[str] = mapped_column(String(32), default="private")

    project: Mapped[Project] = relationship(back_populates="repositories")
    tasks: Mapped[list[Task]] = relationship(back_populates="repository")


class Task(TimestampedModel):
    """A user's request for an isolated AI coding execution."""

    __tablename__ = "tasks"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    repository_id: Mapped[UUID] = mapped_column(
        ForeignKey("repositories.id"), index=True
    )
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"),
        default=TaskStatus.QUEUED,
        index=True,
    )
    base_branch: Mapped[str] = mapped_column(String(255))
    agent_branch: Mapped[str | None] = mapped_column(String(255))
    max_iterations: Mapped[int] = mapped_column(default=20)
    timeout_seconds: Mapped[int] = mapped_column(default=3_600)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="tasks")
    repository: Mapped[Repository] = relationship(back_populates="tasks")
    created_by: Mapped[User] = relationship(back_populates="created_tasks")
    agent_sessions: Mapped[list[AgentSession]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    events: Mapped[list[TaskEvent]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class AgentSession(TimestampedModel):
    """One worker-owned execution attempt for a task."""

    __tablename__ = "agent_sessions"

    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="created", index=True)
    worker_id: Mapped[str | None] = mapped_column(String(255))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    task: Mapped[Task] = relationship(back_populates="agent_sessions")


class TaskEvent(TimestampedModel):
    """An append-only audit event emitted during task execution."""

    __tablename__ = "task_events"

    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[str] = mapped_column(Text)

    task: Mapped[Task] = relationship(back_populates="events")
