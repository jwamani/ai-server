# Backend

The backend will be a Python application using FastAPI, SQLAlchemy, Alembic,
Celery, and PostgreSQL. Source packages follow dependency direction:

`api` and `worker` -> `application` -> `domain` <- `infrastructure`

No sandbox, Git, queue, database, or model-provider SDK calls should appear in
the `domain` package.
