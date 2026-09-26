"""Task management endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.api.dependencies import CurrentUser, SessionDependency
from src.api.schemas import CreateTaskRequest, TaskResponse
from src.domain.task import TaskStatus
from src.infrastructure.database.models import ProjectMember, Repository, Task
from src.worker.tasks import enqueue_task

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])


def to_task_response(task: Task) -> TaskResponse:
    """Map a persistence model to the stable task API contract."""

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        repository_id=task.repository_id,
        created_by_id=task.created_by_id,
        trace_id=task.trace_id,
        title=task.title,
        description=task.description,
        status=task.status.value,
        base_branch=task.base_branch,
        agent_branch=task.agent_branch,
        max_iterations=task.max_iterations,
        timeout_seconds=task.timeout_seconds,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: UUID,
    payload: CreateTaskRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> TaskResponse:
    """Create a coding task for a project."""

    # Verify user is a member of the project
    membership = session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
        )

    # Verify repository belongs to project
    repository = session.scalar(
        select(Repository).where(
            Repository.id == payload.repository_id, Repository.project_id == project_id
        )
    )
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found in this project.",
        )

    task = Task(
        project_id=project_id,
        repository_id=payload.repository_id,
        created_by_id=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        status=TaskStatus.QUEUED,
        base_branch=payload.base_branch.strip(),
        max_iterations=payload.max_iterations,
        timeout_seconds=payload.timeout_seconds,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    enqueue_task(task.id)
    return to_task_response(task)


@router.get("", response_model=list[TaskResponse])
def list_tasks(
    project_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> list[TaskResponse]:
    """List tasks for a project."""

    # Verify user is a member of the project
    membership = session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
        )

    statement = (
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.created_at.desc())
    )
    tasks = session.scalars(statement).all()
    return [to_task_response(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    project_id: UUID,
    task_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> TaskResponse:
    """Get a specific task."""

    # Verify user is a member of the project
    membership = session.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
        )

    statement = select(Task).where(Task.id == task_id, Task.project_id == project_id)
    task = session.scalar(statement)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )
    return to_task_response(task)
