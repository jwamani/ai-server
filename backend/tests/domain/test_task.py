"""Tests for the task lifecycle policy."""

import pytest

from src.domain.task import (
    InvalidTaskTransitionError,
    TaskStatus,
    can_transition,
    require_transition,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (TaskStatus.QUEUED, TaskStatus.INITIALIZING),
        (TaskStatus.RUNNING, TaskStatus.VERIFYING),
        (TaskStatus.VERIFYING, TaskStatus.RUNNING),
        (TaskStatus.VERIFYING, TaskStatus.COMPLETED),
        (TaskStatus.INITIALIZING, TaskStatus.CANCELLED),
    ],
)
def test_allows_valid_task_transition(current: TaskStatus, target: TaskStatus) -> None:
    """Permitted lifecycle edges are accepted."""

    assert can_transition(current, target)
    require_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (TaskStatus.QUEUED, TaskStatus.COMPLETED),
        (TaskStatus.COMPLETED, TaskStatus.RUNNING),
        (TaskStatus.CANCELLED, TaskStatus.INITIALIZING),
        (TaskStatus.FAILED, TaskStatus.QUEUED),
    ],
)
def test_rejects_invalid_task_transition(current: TaskStatus, target: TaskStatus) -> None:
    """Illegal lifecycle edges fail with a domain-specific error."""

    assert not can_transition(current, target)
    with pytest.raises(InvalidTaskTransitionError):
        require_transition(current, target)
