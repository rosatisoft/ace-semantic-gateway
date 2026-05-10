from fastapi.testclient import TestClient

from gateway.api import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "ace-semantic-gateway"


def test_analyze_endpoint_routes_operational():
    response = client.post(
        "/analyze",
        json={
            "costs": {
                "conceptual": 0.82,
                "operational": 0.24,
                "narrative": 0.88,
            },
            "coherence_risk": 0.08,
            "profile": "enterprise",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "ROUTE_OPERATIONAL"
    assert data["processing_mode"] == "full"
    assert data["route"] == "operational"