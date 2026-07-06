def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_city_vitals_legacy_route(client):
    response = client.get("/api/city-vitals")
    assert response.status_code == 200
    body = response.json()
    assert "weather" in body
    assert "community_health_score" in body


def test_city_vitals_v1_route(client):
    response = client.get("/api/v1/city-vitals")
    assert response.status_code == 200


def test_assistant_ask(client):
    response = client.post(
        "/api/assistant/ask",
        json={"question": "Is it safe to jog now?", "session_id": "pytest-session"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "outdoor_safety"
    assert "recommendation" in body
