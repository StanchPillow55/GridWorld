from typing import Any, List, Tuple
import numpy as np
from backend.app.controllers.base import BaseController
from backend.app.schemas import (
    ActionProposal,
    ActionType,
    CandidateAction,
    ProposalRoundRecord
)


class SimpleHeuristicController(BaseController):
    """
    Controller 2: Simple Deterministic Heuristic.
    Pure rule-based greedy switching without look-ahead power flow simulation.
    Strictly 0 simulation calls.
    """

    def __init__(self, overload_threshold: float = 0.95):
        super().__init__(name="Simple Deterministic Heuristic", controller_type="simple_heuristic")
        self.overload_threshold = overload_threshold

    def act(
        self,
        observation: Any,
        candidates: List[CandidateAction],
        adapter: Any,
        step_idx: int = 1
    ) -> Tuple[ActionProposal, List[ProposalRoundRecord]]:
        # 1. Reconnect any disconnected line if available
        line_status = observation.line_status
        disconnected = np.where(~line_status)[0]
        if len(disconnected) > 0:
            reconnect_id = int(disconnected[0])
            for c in candidates:
                if c.action_type == ActionType.SWITCH_LINE and c.target_id == reconnect_id:
                    return ActionProposal(
                        action_id=c.action_id,
                        action_type=c.action_type,
                        target_id=reconnect_id,
                        rationale=f"Greedy reconnection of disconnected Line {reconnect_id} without forecast."
                    ), []

        # 2. Check if peak line rho exceeds threshold
        max_rho = float(np.max(observation.rho))
        if max_rho >= self.overload_threshold:
            worst_line = int(np.argmax(observation.rho))
            for c in candidates:
                if c.action_type == ActionType.SWITCH_LINE and c.target_id == worst_line:
                    return ActionProposal(
                        action_id=c.action_id,
                        action_type=c.action_type,
                        target_id=worst_line,
                        rationale=f"Greedy disconnection of overloaded Line {worst_line} (rho: {max_rho:.2f})."
                    ), []

        # 3. Default to NOOP
        return ActionProposal(
            action_id="A0",
            action_type=ActionType.NOOP,
            rationale=f"Grid thermal loading within limit ({max_rho:.2f} < {self.overload_threshold:.2f}). No intervention."
        ), []
