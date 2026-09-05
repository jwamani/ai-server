"""Project management endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.api.dependencies import CurrentUser, SessionDependency
from src.api.schemas import CreateProjectRequest, ProjectResponse
from src.domain.project import ProjectRole
from src.infrastructure.database.models import Project, ProjectMember

router = APIRouter(prefix="/projects", tags=["projects"])


def to_project_response(project: Project) -> ProjectResponse:
    """Map a persistence model to the stable project API contract."""

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        default_branch=project.default_branch,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ProjectResponse:
    """Create a project and grant its creator the owner role."""

    project = Project(
        owner_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description is not None else None,
        default_branch=payload.default_branch.strip(),
    )
    session.add(project)
    session.flush()
    session.add(
        ProjectMember(project_id=project.id, user_id=current_user.id, role=ProjectRole.OWNER)
    )
    session.commit()
    session.refresh(project)
    return to_project_response(project)


@router.get("", response_model=list[ProjectResponse])
def list_projects(current_user: CurrentUser, session: SessionDependency) -> list[ProjectResponse]:
    """List projects the authenticated user is allowed to access."""

    statement = (
        select(Project)
        .join(ProjectMember)
        .where(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    projects = session.scalars(statement).all()
    return [to_project_response(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> ProjectResponse:
    """Return one project only when the caller is a member."""

    statement = (
        select(Project)
        .join(ProjectMember)
        .where(Project.id == project_id, ProjectMember.user_id == current_user.id)
    )
    project = session.scalar(statement)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return to_project_response(project)
