import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple
import numpy as np

from backend.app.schemas import (
    ExperimentRunRequest,
    ExperimentRecord,
    ReplayData,
    ControllerType,
    ActionProposal,
    ActionType
)
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter
from backend.app.simulator.scenarios import get_scenario
from backend.app.controllers.noop import NoopController
from backend.app.controllers.heuristic import HeuristicController
from backend.app.controllers.ai_controller import AIController
from backend.app.evaluation.metrics import compute_metrics
from backend.app.evaluation.replay import build_replay_data
from backend.app.persistence.experiments import save_experiment_record


def get_controller(controller_type: ControllerType):
    if controller_type == ControllerType.NOOP:
        return NoopController()
    elif controller_type == ControllerType.HEURISTIC:
        return HeuristicController()
    elif controller_type == ControllerType.AI:
        return AIController()
    else:
        raise ValueError(f"Unknown controller type: {controller_type}")


class ExperimentRunner:
    """Executes controlled simulation experiments and collects metrics & replay data."""

    def __init__(self, adapter: Optional[Grid2OpAdapter] = None):
        self.adapter = adapter or Grid2OpAdapter()

    def run_experiment(self, req: ExperimentRunRequest) -> Tuple[ExperimentRecord, ReplayData]:
        scenario = get_scenario(req.scenario_id)
        seed = req.seed if req.seed is not None else scenario.seed
        max_steps = req.max_steps if req.max_steps is not None else scenario.max_steps

        controller = get_controller(req.controller_type)
        controller.reset()

        env = self.adapter.env
        env.seed(seed)
        obs = env.reset()

        start_time = time.perf_counter()
        steps = []
        invalid_actions = 0
        actions_summary = []

        # Record initial step 0 observation
        init_step = self.adapter.observation_to_step(
            obs=obs,
            step_idx=0,
            action_taken=ActionProposal(action_type=ActionType.NOOP, rationale="Initial state"),
            reward=0.0,
            done=False
        )
        steps.append(init_step)

        # Map disturbances by step
        disturbances_by_step = {d.step: d for d in scenario.disturbances}

        for step_idx in range(1, max_steps + 1):
            # Check for scheduled physical disturbance (e.g. tree strike, equipment outage)
            if step_idx in disturbances_by_step:
                dist = disturbances_by_step[step_idx]
                if dist.action == "disconnect":
                    try:
                        fault_act = env.action_space({"set_line_status": [(dist.line_id, -1)]})
                        obs, _, done, _ = env.step(fault_act)
                        actions_summary.append(f"Step {step_idx}: Physical disturbance: Line {dist.line_id} forced offline.")
                        if done:
                            steps.append(
                                self.adapter.observation_to_step(
                                    obs=obs,
                                    step_idx=step_idx,
                                    action_taken=ActionProposal(
                                        action_type=ActionType.SWITCH_LINE,
                                        target_id=dist.line_id,
                                        rationale=f"Forced outage of Line {dist.line_id}"
                                    ),
                                    reward=-10.0,
                                    done=True,
                                    done_reason="Blackout triggered by external disturbance"
                                )
                            )
                            break
                    except Exception:
                        pass

            # Controller decides action
            proposal = controller.act(obs)
            g2op_action, is_valid = self.adapter.create_grid2op_action(proposal)
            if not is_valid:
                invalid_actions += 1

            # Step physical environment
            obs, reward, done, info = env.step(g2op_action)

            # Record step observation
            done_reason = None
            if done:
                done_reason = "Episode terminated (grid blackout or line cascading failure)"

            step_obs = self.adapter.observation_to_step(
                obs=obs,
                step_idx=step_idx,
                action_taken=proposal,
                reward=reward,
                done=done,
                done_reason=done_reason
            )
            steps.append(step_obs)

            if proposal.action_type != ActionType.NOOP:
                actions_summary.append(f"Step {step_idx} ({req.controller_type.value}): {proposal.rationale}")

            if done:
                break

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        metrics = compute_metrics(
            steps=steps,
            max_steps=max_steps,
            execution_time_ms=exec_time_ms,
            invalid_actions=invalid_actions
        )

        exp_id = f"exp_{req.scenario_id}_{req.controller_type.value}_{uuid.uuid4().hex[:6]}"
        topology = self.adapter.get_topology()

        record = ExperimentRecord(
            id=exp_id,
            scenario_id=req.scenario_id,
            controller_type=req.controller_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metrics=metrics,
            actions_summary=actions_summary
        )

        replay = build_replay_data(
            experiment_id=exp_id,
            scenario_id=req.scenario_id,
            controller_type=req.controller_type,
            topology=topology,
            metrics=metrics,
            steps=steps
        )

        save_experiment_record(record, replay)
        return record, replay
