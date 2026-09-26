"""Add trace IDs to task execution records.

Revision ID: 20260926_0005
Revises: 20260926_0004
Create Date: 2026-09-26 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260926_0005"
down_revision: str | Sequence[str] | None = "20260926_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add and backfill trace IDs for tasks, sessions, and events."""

    op.add_column("tasks", sa.Column("trace_id", sa.Uuid(), nullable=True))
    op.execute("UPDATE tasks SET trace_id = gen_random_uuid() WHERE trace_id IS NULL")
    op.alter_column("tasks", "trace_id", nullable=False)
    op.create_index("ix_tasks_trace_id", "tasks", ["trace_id"], unique=True)

    op.add_column("agent_sessions", sa.Column("trace_id", sa.Uuid(), nullable=True))
    op.execute(
        "UPDATE agent_sessions SET trace_id = tasks.trace_id "
        "FROM tasks WHERE agent_sessions.task_id = tasks.id"
    )
    op.alter_column("agent_sessions", "trace_id", nullable=False)
    op.create_index(
        "ix_agent_sessions_trace_id", "agent_sessions", ["trace_id"], unique=False
    )

    op.add_column("task_events", sa.Column("trace_id", sa.Uuid(), nullable=True))
    op.execute(
        "UPDATE task_events SET trace_id = tasks.trace_id "
        "FROM tasks WHERE task_events.task_id = tasks.id"
    )
    op.alter_column("task_events", "trace_id", nullable=False)
    op.create_index(
        "ix_task_events_trace_id", "task_events", ["trace_id"], unique=False
    )


def downgrade() -> None:
    """Remove trace IDs from execution records."""

    op.drop_index("ix_task_events_trace_id", table_name="task_events")
    op.drop_column("task_events", "trace_id")
    op.drop_index("ix_agent_sessions_trace_id", table_name="agent_sessions")
    op.drop_column("agent_sessions", "trace_id")
    op.drop_index("ix_tasks_trace_id", table_name="tasks")
    op.drop_column("tasks", "trace_id")
