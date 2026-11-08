from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_api_environment():
    res = client.get("/api/environment")
    assert res.status_code == 200
    data = res.json()
    assert data["n_sub"] == 14
    assert data["n_line"] == 20
    assert len(data["substations"]) == 14


def test_api_scenarios():
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    assert any(s["id"] == "case14_normal" for s in data)


def test_api_run_experiment():
    payload = {
        "scenario_id": "case14_normal",
        "controller_type": "noop",
        "max_steps": 3
    }
    res = client.post("/api/experiments", json=payload)
    assert res.status_code == 200
    rec = res.json()
    assert "id" in rec
    assert rec["metrics"]["survival_steps"] >= 1

    # Verify we can fetch replay
    exp_id = rec["id"]
    rep_res = client.get(f"/api/experiments/{exp_id}/replay")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["experiment_id"] == exp_id
    assert len(rep_data["steps"]) >= 2
