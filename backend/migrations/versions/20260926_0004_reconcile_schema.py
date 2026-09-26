"""Reconcile the email index with the ORM schema.

Revision ID: 20260926_0004
Revises: 20260926_0003
Create Date: 2026-09-26 00:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260926_0004"
down_revision: str | Sequence[str] | None = "20260926_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove the redundant non-unique email index."""

    op.drop_index("ix_users_email", table_name="users")


def downgrade() -> None:
    """Restore the legacy non-unique email index."""

    op.create_index("ix_users_email", "users", ["email"], unique=False)