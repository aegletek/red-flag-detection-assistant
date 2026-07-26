from fastapi.testclient import TestClient

from red_flag_detection_assistant.api import create_app


def test_api_health() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"