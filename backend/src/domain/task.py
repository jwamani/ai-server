"""Task lifecycle rules independent of persistence and delivery mechanisms."""

from enum import StrEnum


class TaskStatus(StrEnum):
    """Persisted states for a coding task."""

    QUEUED = "queued"
    INITIALIZING = "initializing"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


TERMINAL_TASK_STATUSES = frozenset(
    {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
        TaskStatus.TIMEOUT,
    }
)

_ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.QUEUED: frozenset(
        {TaskStatus.INITIALIZING, TaskStatus.CANCELLED, TaskStatus.FAILED}
    ),
    TaskStatus.INITIALIZING: frozenset(
        {
            TaskStatus.RUNNING,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
        }
    ),
    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.VERIFYING,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
        }
    ),
    TaskStatus.VERIFYING: frozenset(
        {
            TaskStatus.RUNNING,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
            TaskStatus.TIMEOUT,
        }
    ),
    TaskStatus.COMPLETED: frozenset(),
    TaskStatus.FAILED: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
    TaskStatus.TIMEOUT: frozenset(),
}


class InvalidTaskTransitionError(ValueError):
    """Raised when a task state change violates the lifecycle policy."""


def can_transition(current: TaskStatus, target: TaskStatus) -> bool:
    """Return whether the lifecycle permits a transition between statuses."""

    return target in _ALLOWED_TRANSITIONS[current]


def require_transition(current: TaskStatus, target: TaskStatus) -> None:
    """Validate a task transition or raise a precise domain error."""

    if not can_transition(current, target):
        message = f"Task cannot transition from '{current}' to '{target}'."
        raise InvalidTaskTransitionError(message)
