"""PostgreSQL integration coverage for worker idempotency."""

import subprocess
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from celery import Task as CeleryTask
from sqlalchemy import select

from src.config.settings import get_settings
from src.domain.task import TaskStatus
from src.infrastructure.database.models import (
    AgentSession,
    Project,
    ProjectMember,
    Repository,
    Task,
    TaskEvent,
    User,
)
from src.infrastructure.database.session import create_session_factory
from src.worker.execution import TaskExecutionService
from src.worker.tasks import process_task

pytestmark = pytest.mark.integration


@pytest.fixture
def database_session_factory():
    """Provide the configured PostgreSQL session factory or skip the integration test."""

    database_url = get_settings().database_url
    if database_url is None:
        pytest.skip("DATABASE_URL is not configured")
    factory = create_session_factory(database_url)
    try:
        with factory() as session:
            session.execute(select(1))
    except Exception as error:
        pytest.skip(f"Configured PostgreSQL is unavailable: {error}")
    return factory


def _run_git(arguments: list[str], cwd: Path) -> None:
    """Run a Git setup command for the integration fixture."""

    subprocess.run(
        ["git", *arguments], cwd=cwd, check=True, capture_output=True, text=True
    )


def _create_remote(tmp_path: Path) -> Path:
    """Create a local Git remote for worker repository preparation."""

    remote = tmp_path / "remote"
    remote.mkdir()
    _run_git(["init", "--initial-branch", "main"], remote)
    _run_git(["config", "user.email", "integration@example.test"], remote)
    _run_git(["config", "user.name", "Integration Test"], remote)
    (remote / "README.md").write_text("initial\n", encoding="utf-8")
    _run_git(["add", "README.md"], remote)
    _run_git(["commit", "-m", "initial"], remote)
    return remote


def _create_task(session, remote_url: str) -> Task:
    """Create an isolated task graph for one integration test."""

    user = User(
        email=f"worker-{uuid4()}@example.test",
        name="Worker Test",
        password_hash="unused",
    )
    project = Project(owner=user, name=f"Worker Test {uuid4()}")
    project.members.append(ProjectMember(user=user))
    repository = Repository(
        project=project,
        remote_url=remote_url,
    )
    task = Task(
        project=project,
        repository=repository,
        created_by=user,
        title="Idempotency test",
        description="Verify duplicate worker delivery.",
        base_branch="main",
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def _delete_task_graph(session, task_id) -> None:
    """Remove the isolated task graph created by a test."""

    task = session.get(Task, task_id)
    if task is None:
        return
    project = task.project
    user = project.owner
    session.delete(task)
    session.flush()
    session.delete(project)
    session.flush()
    session.delete(user)
    session.commit()


def test_duplicate_claim_creates_one_active_session(
    database_session_factory, tmp_path: Path
) -> None:
    """A second delivery observes the existing claim instead of creating a session."""

    with database_session_factory() as session:
        task = _create_task(session, str(_create_remote(tmp_path)))
        task_id = task.id

    try:
        with database_session_factory() as first_session:
            claimed_task, first_agent_session = TaskExecutionService(first_session).claim(
                task_id
            )
            assert claimed_task.status is TaskStatus.INITIALIZING
            assert first_agent_session is not None
            first_session_id = first_agent_session.id

        with database_session_factory() as second_session:
            observed_task, second_agent_session = TaskExecutionService(second_session).claim(
                task_id
            )
            assert observed_task.status is TaskStatus.INITIALIZING
            assert second_agent_session is not None
            assert second_agent_session.id == first_session_id

        with database_session_factory() as session:
            active_sessions = session.scalars(
                select(AgentSession).where(
                    AgentSession.task_id == task_id,
                    AgentSession.status == "initializing",
                )
            ).all()
            assert len(active_sessions) == 1
    finally:
        with database_session_factory() as session:
            _delete_task_graph(session, task_id)


def test_worker_completion_is_idempotent(
    database_session_factory, tmp_path: Path
) -> None:
    """Repeated delivery after completion does not add sessions or events."""

    with database_session_factory() as session:
        task = _create_task(session, str(_create_remote(tmp_path)))
        task_id = task.id

    try:
        celery_task = cast(CeleryTask, process_task)
        first_result = celery_task.run(str(task_id))
        second_result = celery_task.run(str(task_id))

        assert first_result == second_result
        assert first_result["status"] == TaskStatus.COMPLETED.value

        with database_session_factory() as session:
            task = session.get(Task, task_id)
            assert task is not None
            assert task.status is TaskStatus.COMPLETED
            assert task.trace_id is not None
            sessions = session.scalars(
                select(AgentSession).where(AgentSession.task_id == task_id)
            ).all()
            events = session.scalars(
                select(TaskEvent)
                .where(TaskEvent.task_id == task_id)
                .order_by(TaskEvent.created_at)
            ).all()
            assert len(sessions) == 1
            assert all(event.trace_id == task.trace_id for event in events)
            assert [event.event_type for event in events] == [
                "task.initializing",
                "repository.prepared",
                "repository.status",
                "repository.diff",
                "task.running",
                "agent.started",
                "task.verifying",
                "verification.started",
                "task.completed",
                "agent.completed",
            ]
    finally:
        with database_session_factory() as session:
            _delete_task_graph(session, task_id)
