"""Celery application configuration."""

from celery import Celery  # type: ignore[import-untyped]
from celery.schedules import crontab  # type: ignore[import-untyped]

from src.config.settings import Settings, get_settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    """Create and configure the Celery application."""

    app_settings = settings or get_settings()

    if app_settings.redis_url is None:
        raise RuntimeError("REDIS_URL must be set to use Celery.")

    celery_app = Celery(
        "ai_coding_server",
        broker=app_settings.redis_url,
        backend=app_settings.redis_url,
        include=[
            "src.worker.tasks",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,
        task_soft_time_limit=3540,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        result_expires=86400,
        beat_schedule={
            "cleanup-stale-tasks": {
                "task": "src.worker.tasks.cleanup_stale_tasks",
                "schedule": crontab(minute="*/5"),
            },
        },
    )

    return celery_app


celery_app = create_celery_app()
