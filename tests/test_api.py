from fastapi.testclient import TestClient

import backend.main as main
from backend.database import Database


def test_attempt_endpoint_persists_and_returns_feedback(monkeypatch) -> None:
    # Swap in an isolated database before the application lifespan creates its tables.
    monkeypatch.setattr(main, "database", Database("sqlite://"))

    with TestClient(main.app) as client:
        response = client.post(
            "/v1/attempts",
            json={
                "learner_id": "api-test-learner",
                "expected_text": "red",
                "observed_text": "led",
                "duration_seconds": 0.6,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["asr_provider"] == "deterministic-fixture"
    assert body["observations"][0]["kind"] == "substitution"
    assert body["learner_profile"][0]["phoneme"] == "R"
