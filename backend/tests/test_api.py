from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "backend" in data


def test_api_environment():
    res = client.get("/api/environment")
    assert res.status_code == 200
    data = res.json()
    assert data["n_sub"] == 14
    assert data["n_line"] == 20
    assert len(data["substations"]) == 14
    assert "busbar" in data["busbar_modeling_note"].lower()


def test_api_scenarios_and_splits():
    # All scenarios
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3

    # Development split
    res_dev = client.get("/api/scenarios?split=dev")
    assert res_dev.status_code == 200
    data_dev = res_dev.json()
    assert all(s["split"] == "dev" for s in data_dev)

    # Held-out split
    res_held = client.get("/api/scenarios?split=held_out")
    assert res_held.status_code == 200
    data_held = res_held.json()
    assert all(s["split"] == "held_out" for s in data_held)


def test_api_run_experiment_and_replay():
    payload = {
        "scenario_id": "heldout_chronic_0000_normal",
        "controller_type": "noop",
        "max_steps": 3
    }
    res = client.post("/api/experiments", json=payload)
    assert res.status_code == 200
    rec = res.json()
    assert "id" in rec
    assert rec["metrics"]["survival_steps"] >= 1
    assert "provenance" in rec

    exp_id = rec["id"]
    rep_res = client.get(f"/api/experiments/{exp_id}/replay")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["experiment_id"] == exp_id
    assert len(rep_data["steps"]) >= 2
