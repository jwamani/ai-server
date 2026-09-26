"""Application service for one auditable task execution."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from src.domain.task import TERMINAL_TASK_STATUSES, TaskStatus, require_transition
from src.infrastructure.database.models import AgentSession, Task, TaskEvent
from src.infrastructure.repository import GitRepositoryAdapter


class TaskExecutionService:
    """Coordinate one task execution without coupling it to Celery."""

    def __init__(
        self,
        session: Session,
        repository: GitRepositoryAdapter | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or GitRepositoryAdapter()

    def run(self, task_id: UUID) -> dict[str, str]:
        """Claim, prepare, execute, and finalize one task."""

        task, agent_session = self.claim(task_id)
        if agent_session is None:
            return self._result(task)
        try:
            self._prepare_repository(task)
            self._start_agent(task, agent_session)
            self._verify(task)
            self._complete(task, agent_session)
        except Exception as error:
            self._fail(task_id, error)
            raise
        return self._result(task)

    def claim(self, task_id: UUID) -> tuple[Task, AgentSession | None]:
        """Atomically claim a queued task or reuse its active execution."""

        task = (
            self._session.query(Task)
            .filter(Task.id == task_id)
            .with_for_update()
            .one_or_none()
        )
        if task is None:
            raise ValueError(f"Task '{task_id}' was not found.")
        if task.status in TERMINAL_TASK_STATUSES:
            return task, None
        if task.status != TaskStatus.QUEUED:
            active_session = (
                self._session.query(AgentSession)
                .filter(
                    AgentSession.task_id == task.id,
                    AgentSession.status.in_(("initializing", "running", "verifying")),
                )
                .order_by(AgentSession.created_at.desc())
                .first()
            )
            return task, active_session

        now = datetime.now(UTC)
        agent_session = AgentSession(
            task_id=task.id,
            trace_id=task.trace_id,
            status="initializing",
            worker_id="celery-worker",
            started_at=now,
        )
        self._session.add(agent_session)
        self._transition(task, TaskStatus.INITIALIZING)
        task.started_at = now
        self._session.commit()
        self._session.refresh(task)
        self._session.refresh(agent_session)
        return task, agent_session

    def _prepare_repository(self, task: Task) -> None:
        """Prepare the isolated repository and record its state."""

        with tempfile.TemporaryDirectory(
            prefix=f"ai-task-{task.trace_id}-"
        ) as directory:
            prepared = self._repository.prepare(
                remote_url=task.repository.remote_url,
                base_branch=task.base_branch,
                agent_branch=f"task/{task.id}",
                workspace=Path(directory) / "repository",
            )
            task.agent_branch = prepared.agent_branch
            self._record_event(
                task,
                "repository.prepared",
                {"base_commit": prepared.base_commit, "branch": prepared.agent_branch},
            )
            self._record_event(
                task,
                "repository.status",
                {"status": self._repository.status(prepared.path)},
            )
            self._record_event(
                task, "repository.diff", {"diff": self._repository.diff(prepared.path)}
            )
            self._session.commit()

    def _start_agent(self, task: Task, agent_session: AgentSession) -> None:
        """Advance the task into the agent stage."""

        agent_session.status = "running"
        self._transition(task, TaskStatus.RUNNING)
        self._record_event(task, "agent.started", {"simulated": True})
        self._session.commit()

    def _verify(self, task: Task) -> None:
        """Advance into the verification stage."""

        self._transition(task, TaskStatus.VERIFYING)
        self._record_event(task, "verification.started", {"simulated": True})
        self._session.commit()

    def _complete(self, task: Task, agent_session: AgentSession) -> None:
        """Finalize a successful deterministic execution."""

        completed_at = datetime.now(UTC)
        self._transition(task, TaskStatus.COMPLETED)
        self._record_event(task, "agent.completed", {"simulated": True})
        agent_session.status = "completed"
        agent_session.completed_at = completed_at
        task.completed_at = completed_at
        self._session.commit()

    def _fail(self, task_id: UUID, error: Exception) -> None:
        """Persist failure state after rolling back the failed transaction."""

        self._session.rollback()
        task = self._session.get(Task, task_id)
        if task is None:
            raise error
        agent_session = (
            self._session.query(AgentSession)
            .filter(AgentSession.task_id == task.id)
            .order_by(AgentSession.created_at.desc())
            .first()
        )
        if task.status not in TERMINAL_TASK_STATUSES:
            self._transition(task, TaskStatus.FAILED)
        if agent_session is not None:
            agent_session.status = "failed"
            agent_session.error_message = str(error)
        self._session.commit()

    def _transition(self, task: Task, target: TaskStatus) -> None:
        """Validate and record one task lifecycle transition."""

        require_transition(task.status, target)
        task.status = target
        self._record_event(task, f"task.{target}", {"status": str(target)})

    def _record_event(
        self, task: Task, event_type: str, payload: dict[str, object]
    ) -> None:
        """Add one trace-linked event to the current transaction."""

        self._session.add(
            TaskEvent(
                task_id=task.id,
                trace_id=task.trace_id,
                event_type=event_type,
                payload=json.dumps(payload, default=str),
            )
        )

    @staticmethod
    def _result(task: Task) -> dict[str, str]:
        """Build the stable worker result contract."""

        return {
            "task_id": str(task.id),
            "trace_id": str(task.trace_id),
            "status": task.status.value,
        }
