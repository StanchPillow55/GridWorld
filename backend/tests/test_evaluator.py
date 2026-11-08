import pytest
from backend.app.schemas import ExperimentRunRequest, ControllerType
from backend.app.evaluation.runner import ExperimentRunner


@pytest.fixture(scope="module")
def runner():
    return ExperimentRunner()


def test_noop_runner(runner):
    req = ExperimentRunRequest(
        scenario_id="case14_normal",
        controller_type=ControllerType.NOOP,
        max_steps=5
    )
    record, replay = runner.run_experiment(req)
    assert record.id is not None
    assert record.metrics.survival_steps >= 1
    assert record.metrics.max_steps == 5
    assert record.metrics.actions_taken == 0
    assert len(replay.steps) == record.metrics.survival_steps + 1  # includes step 0


def test_heuristic_runner(runner):
    req = ExperimentRunRequest(
        scenario_id="case14_corridor_congest",
        controller_type=ControllerType.HEURISTIC,
        max_steps=8
    )
    record, replay = runner.run_experiment(req)
    assert record.id is not None
    assert record.metrics.survival_steps >= 1
    assert record.metrics.max_steps == 8
    assert record.metrics.peak_line_utilization > 0.0
