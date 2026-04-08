from fastapi.testclient import TestClient

from redsl.api import create_app


def test_create_app_registers_single_health_route():
    app = create_app()
    health_routes = [route for route in app.routes if getattr(route, "path", None) == "/health"]

    assert len(health_routes) == 1


def test_health_endpoint_returns_expected_payload():
    client = TestClient(create_app())

    response = client.get("/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["agent"] == "conscious-refactor"
    assert payload["version"] == "1.2.14"
    assert "memory" in payload
