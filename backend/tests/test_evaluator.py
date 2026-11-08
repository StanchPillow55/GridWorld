import pytest
from backend.app.schemas import ExperimentRunRequest, ControllerType
from backend.app.evaluation.runner import ExperimentRunner


@pytest.fixture(scope="module")
def runner():
    return ExperimentRunner()


def test_evaluator_on_baseline_failure(runner):
    # On dev_chronic_0003_overload, Do-Nothing collapses at step 3
    req = ExperimentRunRequest(
        scenario_id="dev_chronic_0003_overload",
        controller_type=ControllerType.NOOP,
        max_steps=10
    )
    record, replay = runner.run_experiment(req)
    assert record.metrics.hard_failure is True
    assert record.metrics.survived is False
    assert record.metrics.survival_steps == 3
    assert record.metrics.overload_violations > 0
    assert record.metrics.overload_severity > 0.0


def test_evaluator_on_simulation_planner_success(runner):
    # Simulation planner discovers corrective action and survives horizon
    req = ExperimentRunRequest(
        scenario_id="dev_chronic_0003_overload",
        controller_type=ControllerType.SIMULATION_PLANNER,
        max_steps=8,
        forecast_budget=6
    )
    record, replay = runner.run_experiment(req)
    assert record.metrics.hard_failure is False
    assert record.metrics.survived is True
    assert record.metrics.survival_steps == 8
    assert record.metrics.resource_usage.simulation_calls > 0
