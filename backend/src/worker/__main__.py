"""Worker entrypoint for running the Celery worker."""

import sys

from src.config.settings import get_settings
from src.worker.celery_app import celery_app


def main() -> int:
    """Run the Celery worker."""

    settings = get_settings()
    if settings.redis_url is None:
        print("ERROR: REDIS_URL must be set to run the worker.", file=sys.stderr)
        return 1

    # Start the worker
    celery_app.worker_main(
        argv=[
            "worker",
            "--loglevel=INFO",
            "--concurrency=1",
            "--pool=solo",  # Use solo pool for Windows compatibility
        ]
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
