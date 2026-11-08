from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple
from backend.app.schemas import (
    ActionProposal,
    CandidateAction,
    ProposalRoundRecord,
    ResourceUsage
)


class BaseController(ABC):
    """Abstract base class for all GridWorld controllers."""

    def __init__(self, name: str, controller_type: str):
        self.name = name
        self.controller_type = controller_type
        self.resource_usage = ResourceUsage()
        self.fallback_used = False

    @abstractmethod
    def act(
        self,
        observation: Any,
        candidates: List[CandidateAction],
        adapter: Any,
        step_idx: int = 1
    ) -> Tuple[ActionProposal, List[ProposalRoundRecord]]:
        """
        Given current observation, action catalog, and adapter, return:
        (chosen_action_proposal, proposal_round_records)
        """
        pass

    def reset(self):
        """Reset internal telemetry and state before an episode."""
        self.resource_usage = ResourceUsage()
        self.fallback_used = False
