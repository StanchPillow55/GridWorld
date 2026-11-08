import numpy as np
from typing import Any, List, Optional
from backend.app.controllers.base import BaseController
from backend.app.schemas import ActionProposal, ActionType


class HeuristicController(BaseController):
    """
    Simulation-guided heuristic controller.
    Monitors thermal line loading (rho) and uses Grid2Op's observation simulation
    to evaluate candidate topological reconfigurations, selecting the action that
    minimizes peak line congestion.
    """

    def __init__(self, overload_threshold: float = 0.90):
        super().__init__(name="Simulation-Guided Heuristic")
        self.overload_threshold = overload_threshold

    def act(self, observation: Any, legal_actions: Optional[List[Any]] = None) -> ActionProposal:
        max_rho = float(np.max(observation.rho))

        # Check if lines are disconnected and can be reconnected safely
        line_status = observation.line_status
        disconnected_lines = np.where(~line_status)[0]

        # 1. If safe and disconnected lines exist, test reconnecting them
        if disconnected_lines.size > 0:
            for line_id in disconnected_lines:
                try:
                    action = observation.action_space({"set_line_status": [(int(line_id), 1)]})
                    sim_obs, _, _, _ = observation.simulate(action)
                    if sim_obs is not None and np.max(sim_obs.rho) < 0.95:
                        return ActionProposal(
                            action_type=ActionType.SWITCH_LINE,
                            target_id=int(line_id),
                            rationale=f"Safely reconnected transmission line {line_id}; simulated peak rho is {float(np.max(sim_obs.rho)):.2f}."
                        )
                except Exception:
                    continue

        # 2. If grid is under normal operating limit, maintain current state
        if max_rho < self.overload_threshold:
            return ActionProposal(
                action_type=ActionType.NOOP,
                rationale=f"Thermal loading nominal (peak rho: {max_rho:.2f} < {self.overload_threshold:.2f})."
            )

        # 3. Congestion detected: search candidate topology changes to alleviate peak rho
        best_action_proposal = ActionProposal(
            action_type=ActionType.NOOP,
            rationale=f"Congestion present (peak rho: {max_rho:.2f}), but no candidate action lowered overload risk."
        )
        min_simulated_peak = max_rho

        # Test reconnecting or switching candidate lines connected to the highest-loaded substation
        worst_line = int(np.argmax(observation.rho))

        # Evaluate switching lines or bus elements around the worst line
        candidate_line_ids = [worst_line]
        for line_id in candidate_line_ids:
            try:
                # Test switching line status
                new_status = -1 if line_status[line_id] else 1
                action = observation.action_space({"change_line_status": [line_id]})
                sim_obs, _, _, _ = observation.simulate(action)
                if sim_obs is not None:
                    sim_peak = float(np.max(sim_obs.rho))
                    if sim_peak < min_simulated_peak:
                        min_simulated_peak = sim_peak
                        best_action_proposal = ActionProposal(
                            action_type=ActionType.SWITCH_LINE,
                            target_id=line_id,
                            rationale=f"Switched status of line {line_id} to relieve congestion (reduced peak rho from {max_rho:.2f} to {sim_peak:.2f})."
                        )
            except Exception:
                continue

        return best_action_proposal
