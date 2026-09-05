"""Tests for process health reporting."""

import anyio
import httpx

from src.main import create_app


def test_health_reports_running_api() -> None:
    """The health endpoint exposes a stable operational response."""

    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/health")

    response = anyio.run(request_health)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_authentication_routes_require_database_configuration() -> None:
    """Authentication is unavailable until the control-plane database is configured."""

    async def register_without_database() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/auth/register",
                json={
                    "email": "developer@example.test",
                    "name": "Developer",
                    "password": "a-long-development-password",
                },
            )

    response = anyio.run(register_without_database)

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is not configured."}
