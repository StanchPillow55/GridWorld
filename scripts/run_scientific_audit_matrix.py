import os
import json
import time
from pathlib import Path
from backend.app.schemas import ExperimentRunRequest, ControllerType
from backend.app.evaluation.runner import ExperimentRunner
from backend.app.evaluation.replay import reproduce_trajectory_in_fresh_env
from backend.app.simulator.scenarios import BENCHMARK_SCENARIOS

def main():
    print("=" * 80)
    print("GRIDWORLD SCIENTIFIC SUPPLEMENT AUDIT MATRIX EXECUTION")
    print("=" * 80)

    runner = ExperimentRunner()
    scenarios = [
        "dev_chronic_0003_overload",
        "dev_chronic_0001_congest",
        "heldout_chronic_0000_normal",
        "heldout_chronic_0002_corridor"
    ]

    controllers = [
        ControllerType.NOOP,
        ControllerType.SIMPLE_HEURISTIC,
        ControllerType.SIMULATION_PLANNER,
        ControllerType.DIRECT_LLM,
        ControllerType.REFINEMENT_LLM
    ]

    results_matrix = {}
    traces_collected = []

    for sc_id in scenarios:
        sc_config = BENCHMARK_SCENARIOS[sc_id]
        print(f"\n---> SCENARIO: {sc_id} (Split: {sc_config.split.value}, Chronic: {sc_config.chronic_id})")
        results_matrix[sc_id] = {}

        for ctrl in controllers:
            print(f"  Running {ctrl.value}...", end=" ", flush=True)
            req = ExperimentRunRequest(
                scenario_id=sc_id,
                controller_type=ctrl,
                max_steps=10,
                forecast_budget=5,
                max_proposals_per_step=3
            )
            t0 = time.perf_counter()
            record, replay = runner.run_experiment(req)
            elapsed = time.perf_counter() - t0

            # Test fresh reproduction
            is_reproducible, max_div = reproduce_trajectory_in_fresh_env(replay)

            m = record.metrics
            u = m.resource_usage
            print(f"Done in {elapsed:.1f}s | Steps: {m.survival_steps}/{m.max_steps} | Survived: {m.survived} | Peak ρ: {m.peak_line_utilization*100:.1f}% | SimCalls: {u.simulation_calls} | ModelCalls: {u.model_calls} | Fallback: {m.fallback_used} | ReplayDiv: {max_div:.6f}")

            results_matrix[sc_id][ctrl.value] = {
                "survived": m.survived,
                "survival_steps": m.survival_steps,
                "max_steps": m.max_steps,
                "hard_failure": m.hard_failure,
                "peak_rho": m.peak_line_utilization,
                "overload_violations": m.overload_violations,
                "overload_severity": m.overload_severity,
                "actions_taken": m.actions_taken,
                "forecast_mae": m.forecast_mean_absolute_error,
                "simulation_calls": u.simulation_calls,
                "model_calls": u.model_calls,
                "prompt_tokens": u.prompt_tokens,
                "completion_tokens": u.completion_tokens,
                "latency_ms": u.model_latency_ms,
                "fallback_used": m.fallback_used,
                "reproducible": is_reproducible,
                "max_divergence": max_div
            }

            # If refinement LLM had proposals, save sample trace
            for step in replay.steps:
                if len(step.proposals_history) > 1:
                    traces_collected.append({
                        "scenario_id": sc_id,
                        "controller": ctrl.value,
                        "step": step.step,
                        "proposals": [p.model_dump() for p in step.proposals_history],
                        "forecast": step.forecast_verification.model_dump() if step.forecast_verification else None
                    })
                    break

    # Save complete matrix results
    matrix_path = Path("experiments/fixtures/benchmark_matrix_results.json")
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    with open(matrix_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "matrix": results_matrix,
            "sample_refinement_traces": traces_collected[:3]
        }, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Results matrix successfully written to {matrix_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
