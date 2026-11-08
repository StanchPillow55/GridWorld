import pytest
from backend.app.schemas import ExperimentRunRequest, ControllerType
from backend.app.evaluation.runner import ExperimentRunner
from backend.app.persistence.experiments import get_experiment_record, get_experiment_replay


def test_replay_persistence():
    runner = ExperimentRunner()
    req = ExperimentRunRequest(
        scenario_id="case14_normal",
        controller_type=ControllerType.NOOP,
        max_steps=4,
        seed=42
    )
    record, replay = runner.run_experiment(req)

    loaded_record = get_experiment_record(record.id)
    assert loaded_record is not None
    assert loaded_record.id == record.id
    assert loaded_record.metrics.survival_steps == record.metrics.survival_steps

    loaded_replay = get_experiment_replay(record.id)
    assert loaded_replay is not None
    assert loaded_replay.experiment_id == record.id
    assert len(loaded_replay.steps) == len(replay.steps)
    assert loaded_replay.steps[0].max_rho == replay.steps[0].max_rho
