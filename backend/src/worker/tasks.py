"""Celery task definitions for the worker."""

import json
from datetime import UTC, datetime
from uuid import UUID

from celery import Task as CeleryTask, shared_task  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

from src.config.settings import get_settings
from src.domain.task import TERMINAL_TASK_STATUSES, TaskStatus, require_transition
from src.infrastructure.database.models import AgentSession, Task, TaskEvent
from src.infrastructure.database.session import create_session_factory


def enqueue_task(task_id: UUID) -> None:
    """Submit a persisted task to Celery without requiring Redis at API import time."""

    if get_settings().redis_url is None:
        raise RuntimeError("REDIS_URL must be set before enqueueing tasks.")

    from src.worker.celery_app import celery_app

    celery_app.send_task("src.worker.tasks.process_task", args=[str(task_id)])


def _record_event(
    session: Session, task: Task, event_type: str, payload: dict[str, object]
) -> None:
    """Persist one trace-linked task event."""

    session.add(
        TaskEvent(
            task_id=task.id,
            trace_id=task.trace_id,
            event_type=event_type,
            payload=json.dumps(payload, default=str),
        )
    )


def _transition_task(session: Session, task: Task, target: TaskStatus) -> None:
    """Validate and apply one task lifecycle transition."""

    require_transition(task.status, target)
    task.status = target
    _record_event(session, task, f"task.{target}", {"status": str(target)})


@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[untyped-decorator]
def process_task(self: CeleryTask, task_id: str) -> dict[str, str]:
    """Run the deterministic execution lifecycle for one queued task."""

    settings = get_settings()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL must be set to process tasks.")

    session_factory = create_session_factory(settings.database_url)
    with session_factory() as session:
        task = session.get(Task, UUID(task_id))
        if task is None:
            raise ValueError(f"Task '{task_id}' was not found.")
        if task.status in TERMINAL_TASK_STATUSES:
            return {
                "task_id": task_id,
                "trace_id": str(task.trace_id),
                "status": task.status.value,
            }

        now = datetime.now(UTC)
        agent_session = AgentSession(
            task_id=task.id,
            trace_id=task.trace_id,
            status="initializing",
            worker_id="celery-worker",
            started_at=now,
        )
        session.add(agent_session)
        _transition_task(session, task, TaskStatus.INITIALIZING)
        task.started_at = now
        session.commit()

        agent_session.status = "running"
        _transition_task(session, task, TaskStatus.RUNNING)
        _record_event(session, task, "agent.started", {"simulated": True})
        session.commit()

        _transition_task(session, task, TaskStatus.VERIFYING)
        _record_event(session, task, "verification.started", {"simulated": True})
        session.commit()

        completed_at = datetime.now(UTC)
        _transition_task(session, task, TaskStatus.COMPLETED)
        _record_event(session, task, "task.completed", {"simulated": True})
        agent_session.status = "completed"
        agent_session.completed_at = completed_at
        task.completed_at = completed_at
        session.commit()

        return {
            "task_id": task_id,
            "trace_id": str(task.trace_id),
            "status": task.status.value,
        }


@shared_task  # type: ignore[untyped-decorator]
def cleanup_stale_tasks() -> dict[str, int | str]:
    """Periodic task to clean up tasks stuck in non-terminal states."""

    settings = get_settings()
    if settings.database_url is None:
        return {"cleaned": 0, "error": "Database not configured"}

    session_factory = create_session_factory(settings.database_url)
    with session_factory():
        # TODO: Find tasks stuck in INITIALIZING/RUNNING/VERIFYING beyond timeout
        # and transition them to FAILED or TIMEOUT
        pass

    return {"cleaned": 0}
