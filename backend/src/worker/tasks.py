"""Celery task definitions for the worker."""

from uuid import UUID

from celery import Task as CeleryTask  # type: ignore[import-untyped]
from celery import shared_task

from src.config.settings import get_settings
from src.infrastructure.database.session import create_session_factory
from src.worker.execution import TaskExecutionService


def enqueue_task(task_id: UUID) -> None:
    """Submit a persisted task to Celery without requiring Redis at API import time."""

    if get_settings().redis_url is None:
        raise RuntimeError("REDIS_URL must be set before enqueueing tasks.")

    from src.worker.celery_app import celery_app

    celery_app.send_task("src.worker.tasks.process_task", args=[str(task_id)])


@shared_task(bind=True, max_retries=3, default_retry_delay=60)  # type: ignore[untyped-decorator]
def process_task(self: CeleryTask, task_id: str) -> dict[str, str]:
    """Run one task through the execution service."""

    settings = get_settings()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL must be set to process tasks.")

    session_factory = create_session_factory(settings.database_url)
    with session_factory() as session:
        return TaskExecutionService(session).run(UUID(task_id))


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
