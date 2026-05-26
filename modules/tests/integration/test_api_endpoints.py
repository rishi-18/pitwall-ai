"""
Integration tests for FastAPI endpoints.
"""


def test_health_endpoint(api_client):

    resp = api_client.get("/health")

    assert resp.status_code == 200

    assert resp.json()["status"] == "ok"


def test_list_sessions_default_params(
    api_client
):

    resp = api_client.get(
        "/v1/sessions/"
    )

    assert resp.status_code == 200

    data = resp.json()

    assert data["year"] == 2024


def test_pit_strategy_prediction(
    api_client,
    sample_pit_input
):

    resp = api_client.post(
        "/v1/predictions/pit-strategy",
        json=sample_pit_input.model_dump(),
    )

    assert resp.status_code == 200

    data = resp.json()

    assert "recommended_pit_lap" in data
