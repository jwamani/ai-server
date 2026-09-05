"""Tests for process health reporting."""

from fastapi.testclient import TestClient

from src.main import create_app


def test_health_reports_running_api() -> None:
    """The health endpoint exposes a stable operational response."""

    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}
