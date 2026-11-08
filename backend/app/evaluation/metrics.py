from typing import List
import numpy as np
from backend.app.schemas import ExperimentMetrics, StepObservation, ActionType


def compute_metrics(
    steps: List[StepObservation],
    max_steps: int,
    execution_time_ms: float,
    invalid_actions: int = 0
) -> ExperimentMetrics:
    if not steps:
        return ExperimentMetrics(
            survival_steps=0,
            max_steps=max_steps,
            survived=False,
            peak_line_utilization=0.0,
            mean_line_utilization=0.0,
            overload_violations=0,
            actions_taken=0,
            invalid_actions=invalid_actions,
            execution_time_ms=execution_time_ms
        )

    # Step 0 is the initial condition before actions; survival_steps is control steps completed
    survival_steps = max(0, len(steps) - 1)
    survived = survival_steps >= max_steps and not steps[-1].done

    all_rhos = [rho for s in steps for rho in s.line_rhos]
    peak_rho = float(max(all_rhos)) if all_rhos else 0.0
    mean_rho = float(np.mean(all_rhos)) if all_rhos else 0.0

    # Count instances of line overloads (rho >= 1.0)
    overload_violations = sum(1 for rho in all_rhos if rho >= 1.0)

    # Count purposeful actions
    actions_taken = sum(1 for s in steps if s.action_taken.action_type != ActionType.NOOP)

    return ExperimentMetrics(
        survival_steps=survival_steps,
        max_steps=max_steps,
        survived=survived,
        peak_line_utilization=round(peak_rho, 4),
        mean_line_utilization=round(mean_rho, 4),
        overload_violations=overload_violations,
        actions_taken=actions_taken,
        invalid_actions=invalid_actions,
        execution_time_ms=round(execution_time_ms, 2)
    )
