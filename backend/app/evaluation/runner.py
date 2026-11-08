import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, List
import numpy as np

from backend.app.schemas import (
    ExperimentRunRequest,
    ExperimentRecord,
    ReplayData,
    ControllerType,
    ActionProposal,
    ActionType,
    ForecastVerification,
    StepObservation
)
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter
from backend.app.simulator.scenarios import get_scenario
from backend.app.controllers.noop import NoopController
from backend.app.controllers.simple_heuristic import SimpleHeuristicController
from backend.app.controllers.simulation_planner import SimulationGuidedPlanner
from backend.app.controllers.direct_llm import DirectLLMController
from backend.app.controllers.refinement_llm import RefinementLLMController
from backend.app.evaluation.metrics import compute_metrics
from backend.app.evaluation.replay import build_replay_data
from backend.app.persistence.experiments import save_experiment_record


def instantiate_controller(controller_type: ControllerType, forecast_budget: int = 5, max_rounds: int = 3):
    if controller_type == ControllerType.NOOP:
        return NoopController()
    elif controller_type == ControllerType.SIMPLE_HEURISTIC:
        return SimpleHeuristicController()
    elif controller_type == ControllerType.SIMULATION_PLANNER:
        return SimulationGuidedPlanner(forecast_budget=forecast_budget)
    elif controller_type == ControllerType.DIRECT_LLM:
        return DirectLLMController()
    elif controller_type == ControllerType.REFINEMENT_LLM:
        return RefinementLLMController(max_rounds=max_rounds)
    else:
        raise ValueError(f"Unknown controller type: {controller_type}")


class ExperimentRunner:
    """Executes strictly instrumented head-to-head grid control experiments."""

    def __init__(self, adapter: Optional[Grid2OpAdapter] = None):
        self.adapter = adapter or Grid2OpAdapter()

    def run_experiment(self, req: ExperimentRunRequest) -> Tuple[ExperimentRecord, ReplayData]:
        scenario = get_scenario(req.scenario_id)
        seed = req.seed if req.seed is not None else scenario.seed
        max_steps = req.max_steps if req.max_steps is not None else scenario.max_steps

        controller = instantiate_controller(
            controller_type=req.controller_type,
            forecast_budget=req.forecast_budget,
            max_rounds=req.max_proposals_per_step
        )
        controller.reset()

        obs = self.adapter.reset_chronic(chronic_id=scenario.chronic_id, seed=seed)

        start_time = time.perf_counter()
        steps: List[StepObservation] = []
        invalid_actions = 0
        actions_summary = []

        # Record initial step 0 observation
        init_step = self.adapter.observation_to_step(
            obs=obs,
            step_idx=0,
            action_taken=ActionProposal(action_type=ActionType.NOOP, rationale="Initial state at chronic start"),
            reward=0.0,
            done=False
        )
        steps.append(init_step)

        disturbances_by_step = {d.step: d for d in scenario.disturbances}
        env = self.adapter.env

        for step_idx in range(1, max_steps + 1):
            # 1. Check for scheduled physical disturbance (strictly 1 env.step per step_idx)
            if step_idx in disturbances_by_step:
                dist = disturbances_by_step[step_idx]
                if dist.action == "disconnect":
                    try:
                        fault_act = env.action_space({"set_line_status": [(dist.line_id, -1)]})
                        obs, reward, done, info = env.step(fault_act)
                        actions_summary.append(f"Step {step_idx}: Physical disturbance: Line {dist.line_id} forced offline.")

                        step_obs = self.adapter.observation_to_step(
                            obs=obs,
                            step_idx=step_idx,
                            action_taken=ActionProposal(
                                action_type=ActionType.SWITCH_LINE,
                                target_id=dist.line_id,
                                rationale=f"Exogenous physical disturbance: Line {dist.line_id} forced offline."
                            ),
                            reward=reward,
                            done=done,
                            done_reason="Blackout triggered by external disturbance" if done else None,
                            fallback_used=False
                        )
                        steps.append(step_obs)
                        if done:
                            break
                        # Disturbance consumed step_idx; controller responds at next timestep
                        continue
                    except Exception:
                        pass

            # 2. Controller decision cycle
            candidates = self.adapter.get_candidate_actions(obs)

            proposal, proposal_records = controller.act(
                observation=obs,
                candidates=candidates,
                adapter=self.adapter,
                step_idx=step_idx
            )

            # Retrieve forecasted rho from selected proposal round
            forecasted_rho: Optional[float] = None
            for pr in proposal_records:
                if pr.selected:
                    forecasted_rho = pr.simulated_max_rho
                    break

            g2op_action, is_valid = self.adapter.create_grid2op_action(proposal)
            if not is_valid:
                invalid_actions += 1

            # Step physical environment exactly once
            obs, reward, done, info = env.step(g2op_action)

            # Measure forecast verification if simulation occurred
            forecast_verif = None
            actual_max_rho = float(np.max(obs.rho)) if len(obs.rho) > 0 else 0.0
            if forecasted_rho is not None and forecasted_rho < 900.0:
                forecast_verif = ForecastVerification(
                    forecasted_max_rho=forecasted_rho,
                    actual_max_rho=actual_max_rho,
                    forecast_error=round(abs(actual_max_rho - forecasted_rho), 4)
                )

            done_reason = None
            if done:
                exc_list = info.get("exception", [])
                done_reason = f"Grid collapsed: {exc_list[0] if exc_list else 'thermal cascade or power flow divergence'}"

            step_obs = self.adapter.observation_to_step(
                obs=obs,
                step_idx=step_idx,
                action_taken=proposal,
                reward=reward,
                done=done,
                done_reason=done_reason,
                fallback_used=controller.fallback_used
            )
            step_obs.proposals_history = proposal_records
            step_obs.forecast_verification = forecast_verif
            steps.append(step_obs)

            if proposal.action_type != ActionType.NOOP:
                actions_summary.append(f"Step {step_idx} ({req.controller_type.value}): {proposal.rationale}")

            if done:
                break

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0

        provenance = self.adapter.get_provenance_metadata(
            max_steps=max_steps,
            disturbances=scenario.disturbances
        )

        metrics = compute_metrics(
            steps=steps,
            max_steps=max_steps,
            execution_time_ms=exec_time_ms,
            resource_usage=controller.resource_usage,
            invalid_actions=invalid_actions,
            fallback_used=controller.fallback_used
        )

        exp_id = f"exp_{req.scenario_id}_{req.controller_type.value}_{uuid.uuid4().hex[:6]}"
        topology = self.adapter.get_topology()

        record = ExperimentRecord(
            id=exp_id,
            scenario_id=req.scenario_id,
            controller_type=req.controller_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provenance=provenance,
            metrics=metrics,
            actions_summary=actions_summary
        )

        replay = build_replay_data(
            experiment_id=exp_id,
            scenario_id=req.scenario_id,
            controller_type=req.controller_type,
            provenance=provenance,
            topology=topology,
            metrics=metrics,
            steps=steps
        )

        save_experiment_record(record, replay)
        return record, replay
