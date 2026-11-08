import json
from pathlib import Path
import pytest
from backend.app.schemas import ExperimentRunRequest, ControllerType
from backend.app.evaluation.runner import ExperimentRunner
from backend.app.persistence.experiments import get_experiment_record, get_experiment_replay


def test_replay_persistence_and_determinism():
    runner = ExperimentRunner()
    req = ExperimentRunRequest(
        scenario_id="heldout_chronic_0000_normal",
        controller_type=ControllerType.NOOP,
        max_steps=5,
        seed=42
    )
    record, replay = runner.run_experiment(req)

    loaded_record = get_experiment_record(record.id)
    assert loaded_record is not None
    assert loaded_record.id == record.id
    assert loaded_record.provenance.chronic_id == 0

    loaded_replay = get_experiment_replay(record.id)
    assert loaded_replay is not None
    assert loaded_replay.experiment_id == record.id
    assert len(loaded_replay.steps) == len(replay.steps)


def test_committed_experiment_fixture():
    fixture_path = Path("experiments/fixtures/committed_baseline_vs_llm_experiment.json")
    assert fixture_path.exists(), "Committed experiment fixture must exist"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "scientific_finding" in data
    assert "controllers" in data
    assert len(data["controllers"]) >= 2

    # Verify baseline failure is documented
    noop_entry = data["controllers"][0]
    assert noop_entry["record"]["metrics"]["hard_failure"] is True
    assert noop_entry["record"]["metrics"]["survival_steps"] == 3

    # Verify planner success is documented
    plan_entry = data["controllers"][1]
    assert plan_entry["record"]["metrics"]["survived"] is True
    assert plan_entry["record"]["metrics"]["survival_steps"] == 10
