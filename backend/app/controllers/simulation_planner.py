from typing import Any, List, Tuple
import numpy as np
from backend.app.controllers.base import BaseController
from backend.app.schemas import (
    ActionProposal,
    ActionType,
    CandidateAction,
    ProposalRoundRecord
)


class SimulationGuidedPlanner(BaseController):
    """
    Controller 3: Deterministic Simulation-Guided Planner.
    Systematically evaluates candidates using obs.simulate(action, time_step=1)
    within a bounded forecast budget, selecting the candidate that minimizes peak line rho.
    """

    def __init__(self, forecast_budget: int = 5, overload_threshold: float = 0.90):
        super().__init__(name="Simulation-Guided Deterministic Planner", controller_type="simulation_planner")
        self.forecast_budget = forecast_budget
        self.overload_threshold = overload_threshold

    def act(
        self,
        observation: Any,
        candidates: List[CandidateAction],
        adapter: Any,
        step_idx: int = 1
    ) -> Tuple[ActionProposal, List[ProposalRoundRecord]]:
        current_max_rho = float(np.max(observation.rho))
        round_records: List[ProposalRoundRecord] = []

        # If current state is safe, test NOOP first
        best_candidate = candidates[0]
        best_sim_rho = current_max_rho
        best_sim_done = False

        # Limit candidate search to forecast budget
        eval_candidates = candidates[:self.forecast_budget]

        for idx, candidate in enumerate(eval_candidates):
            self.resource_usage.simulation_calls += 1
            proposal = ActionProposal(
                action_id=candidate.action_id,
                action_type=candidate.action_type,
                target_id=candidate.target_id,
                target_bus=candidate.target_bus,
                redispatch_val=candidate.redispatch_val,
                rationale=candidate.description
            )
            g2op_action, is_valid = adapter.create_grid2op_action(proposal)

            sim_max_rho = 999.0
            sim_done = True
            feedback = "Invalid action"

            if is_valid:
                try:
                    sim_obs, sim_r, sim_done, sim_info = observation.simulate(g2op_action, time_step=1)
                    if sim_obs is not None:
                        sim_max_rho = float(np.max(sim_obs.rho))
                        feedback = f"Simulated peak rho: {sim_max_rho:.3f}, done={sim_done}"
                    else:
                        feedback = "Simulation returned null observation (divergence)"
                except Exception as e:
                    feedback = f"Simulation exception: {str(e)}"

            is_selected = False
            # Better candidate found: lower peak rho and does not cause immediate failure
            if not sim_done and sim_max_rho < best_sim_rho:
                best_sim_rho = sim_max_rho
                best_sim_done = False
                best_candidate = candidate

            round_records.append(
                ProposalRoundRecord(
                    round_index=idx + 1,
                    action_id=candidate.action_id,
                    action_type=candidate.action_type,
                    target_id=candidate.target_id,
                    rationale=candidate.description,
                    simulated_max_rho=round(sim_max_rho, 4) if sim_max_rho < 900 else 999.0,
                    simulated_done=sim_done,
                    feedback=feedback,
                    selected=False
                )
            )

        # Mark selected candidate
        for r in round_records:
            if r.action_id == best_candidate.action_id:
                r.selected = True
                break

        chosen_proposal = ActionProposal(
            action_id=best_candidate.action_id,
            action_type=best_candidate.action_type,
            target_id=best_candidate.target_id,
            target_bus=best_candidate.target_bus,
            redispatch_val=best_candidate.redispatch_val,
            rationale=(
                f"Selected {best_candidate.action_id} after evaluating {len(eval_candidates)} candidates; "
                f"projected peak rho: {best_sim_rho:.3f} (baseline: {current_max_rho:.3f})."
            )
        )

        return chosen_proposal, round_records
