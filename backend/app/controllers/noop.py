from typing import Any, List, Tuple
from backend.app.controllers.base import BaseController
from backend.app.schemas import (
    ActionProposal,
    ActionType,
    CandidateAction,
    ProposalRoundRecord
)


class NoopController(BaseController):
    """
    Controller 1: Do-Nothing Baseline.
    Passively monitors grid state without intervention. Zero simulation and zero model calls.
    """

    def __init__(self):
        super().__init__(name="Do-Nothing Baseline", controller_type="noop")

    def act(
        self,
        observation: Any,
        candidates: List[CandidateAction],
        adapter: Any,
        step_idx: int = 1
    ) -> Tuple[ActionProposal, List[ProposalRoundRecord]]:
        proposal = ActionProposal(
            action_id="A0",
            action_type=ActionType.NOOP,
            rationale="Passively monitor grid state without intervention (Do-Nothing baseline)."
        )
        return proposal, []
