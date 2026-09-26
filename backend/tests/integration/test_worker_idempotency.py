"""PostgreSQL integration coverage for worker idempotency."""

from uuid import uuid4
from typing import cast

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
from src.worker.tasks import _claim_task, process_task

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


def _create_task(session) -> Task:
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
        remote_url=f"https://example.test/{uuid4()}.git",
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


def test_duplicate_claim_creates_one_active_session(database_session_factory) -> None:
    """A second delivery observes the existing claim instead of creating a session."""

    with database_session_factory() as session:
        task = _create_task(session)
        task_id = task.id

    try:
        with database_session_factory() as first_session:
            claimed_task, first_agent_session = _claim_task(first_session, task_id)
            assert claimed_task.status is TaskStatus.INITIALIZING
            assert first_agent_session is not None
            first_session_id = first_agent_session.id

        with database_session_factory() as second_session:
            observed_task, second_agent_session = _claim_task(second_session, task_id)
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


def test_worker_completion_is_idempotent(database_session_factory) -> None:
    """Repeated delivery after completion does not add sessions or events."""

    with database_session_factory() as session:
        task = _create_task(session)
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
