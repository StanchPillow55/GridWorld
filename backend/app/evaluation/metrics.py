from typing import List
import numpy as np
from backend.app.schemas import (
    ExperimentMetrics,
    StepObservation,
    ActionType,
    ResourceUsage
)


def compute_metrics(
    steps: List[StepObservation],
    max_steps: int,
    execution_time_ms: float,
    resource_usage: ResourceUsage,
    invalid_actions: int = 0,
    fallback_used: bool = False
) -> ExperimentMetrics:
    if not steps:
        return ExperimentMetrics(
            survival_steps=0,
            max_steps=max_steps,
            survived=False,
            hard_failure=True,
            peak_line_utilization=0.0,
            mean_line_utilization=0.0,
            overload_violations=0,
            overload_severity=0.0,
            actions_taken=0,
            invalid_actions=invalid_actions,
            forecast_mean_absolute_error=0.0,
            execution_time_ms=execution_time_ms,
            resource_usage=resource_usage,
            fallback_used=fallback_used
        )

    # Step 0 is initial reset condition; survival_steps is control steps completed
    survival_steps = max(0, len(steps) - 1)
    last_step = steps[-1]
    hard_failure = bool(last_step.done and survival_steps < max_steps)
    survived = bool(survival_steps >= max_steps and not last_step.done)

    # Collect all line utilizations across all timesteps
    all_rhos = [float(rho) for s in steps for rho in s.line_rhos]
    peak_rho = float(max(all_rhos)) if all_rhos else 0.0
    mean_rho = float(np.mean(all_rhos)) if all_rhos else 0.0

    # Overload statistics
    overload_violations = sum(1 for rho in all_rhos if rho >= 1.0)
    overload_severity = float(sum((rho - 1.0) for rho in all_rhos if rho > 1.0))

    # Action counts
    actions_taken = sum(1 for s in steps if s.action_taken.action_type != ActionType.NOOP)

    # Forecast vs Actual verification error
    forecast_errors = [
        s.forecast_verification.forecast_error
        for s in steps
        if s.forecast_verification is not None
    ]
    mean_forecast_mae = float(np.mean(forecast_errors)) if forecast_errors else 0.0

    # Any fallback used across steps
    overall_fallback = fallback_used or any(s.fallback_used for s in steps)

    return ExperimentMetrics(
        survival_steps=survival_steps,
        max_steps=max_steps,
        survived=survived,
        hard_failure=hard_failure,
        peak_line_utilization=round(peak_rho, 4),
        mean_line_utilization=round(mean_rho, 4),
        overload_violations=overload_violations,
        overload_severity=round(overload_severity, 4),
        actions_taken=actions_taken,
        invalid_actions=invalid_actions,
        forecast_mean_absolute_error=round(mean_forecast_mae, 4),
        execution_time_ms=round(execution_time_ms, 2),
        resource_usage=resource_usage,
        fallback_used=overall_fallback
    )
