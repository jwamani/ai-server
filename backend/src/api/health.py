"""Operational health endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel

from src import __version__

router = APIRouter(tags=["operations"])


class HealthResponse(BaseModel):
    """Minimal process-health response."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health() -> HealthResponse:
    """Confirm that the API process is accepting requests."""

    return HealthResponse(status="ok", version=__version__)
