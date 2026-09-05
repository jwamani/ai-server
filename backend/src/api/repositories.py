"""Repository registration endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from src.api.dependencies import CurrentUser, SessionDependency
from src.api.schemas import CreateRepositoryRequest, RepositoryResponse
from src.infrastructure.database.models import ProjectMember, Repository

router = APIRouter(prefix="/projects/{project_id}/repositories", tags=["repositories"])


def to_repository_response(repo: Repository) -> RepositoryResponse:
    """Map a persistence model to the stable repository API contract."""

    return RepositoryResponse(
        id=repo.id,
        project_id=repo.project_id,
        provider=repo.provider,
        remote_url=repo.remote_url,
        default_branch=repo.default_branch,
        visibility=repo.visibility,
    )


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    project_id: UUID,
    payload: CreateRepositoryRequest,
    current_user: CurrentUser,
    session: SessionDependency,
) -> RepositoryResponse:
    """Register a repository for a project."""

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

    repository = Repository(
        project_id=project_id,
        provider=payload.provider,
        remote_url=payload.remote_url,
        default_branch=payload.default_branch,
        visibility=payload.visibility,
    )
    session.add(repository)
    try:
        session.commit()
    except Exception as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A repository with this remote URL already exists.",
        ) from error
    session.refresh(repository)
    return to_repository_response(repository)


@router.get("", response_model=list[RepositoryResponse])
def list_repositories(
    project_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> list[RepositoryResponse]:
    """List repositories for a project."""

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
        select(Repository)
        .where(Repository.project_id == project_id)
        .order_by(Repository.created_at.desc())
    )
    repositories = session.scalars(statement).all()
    return [to_repository_response(repo) for repo in repositories]


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository(
    project_id: UUID,
    repository_id: UUID,
    current_user: CurrentUser,
    session: SessionDependency,
) -> RepositoryResponse:
    """Get a specific repository."""

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

    statement = select(Repository).where(
        Repository.id == repository_id, Repository.project_id == project_id
    )
    repository = session.scalar(statement)
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found."
        )
    return to_repository_response(repository)
