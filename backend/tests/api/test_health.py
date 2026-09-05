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
