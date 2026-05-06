from fastapi.testclient import TestClient

from gateway.api import app


client = TestClient(app)


def test_guard_routes_narrative():
    response = client.post(
        "/guard",
        json={"text": "The dragon guarded the ancient kingdom"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "ROUTE_NARRATIVE"
    assert data["processing_mode"] == "full"
    assert data["route"] == "narrative"
    assert data["allow_llm"] is True


def test_guard_routes_operational():
    response = client.post(
        "/guard",
        json={"text": "Paris is the capital of France"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "ROUTE_OPERATIONAL"
    assert data["processing_mode"] == "full"
    assert data["route"] == "operational"
    assert data["allow_llm"] is True


def test_guard_detects_contradiction():
    response = client.post(
        "/guard",
        json={"text": "Truth is true and false at the same time"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["decision"] == "CONTRADICTION_RISK"
    assert data["processing_mode"] == "short"
    assert data["allow_llm"] is False