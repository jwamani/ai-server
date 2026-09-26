"""Enforce one active worker session per task.

Revision ID: 20260926_0006
Revises: 20260926_0005
Create Date: 2026-09-26 00:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260926_0006"
down_revision: str | Sequence[str] | None = "20260926_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow only one initializing/running/verifying session per task."""

    op.create_index(
        "uq_agent_sessions_active_task",
        "agent_sessions",
        ["task_id"],
        unique=True,
        postgresql_where="status IN ('initializing', 'running', 'verifying')",
    )


def downgrade() -> None:
    """Remove the active-session uniqueness constraint."""

    op.drop_index("uq_agent_sessions_active_task", table_name="agent_sessions")