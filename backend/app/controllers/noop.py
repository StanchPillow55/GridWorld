from typing import Any, List, Optional
from backend.app.controllers.base import BaseController
from backend.app.schemas import ActionProposal, ActionType


class NoopController(BaseController):
    """Baseline controller that takes no action (Do-Nothing)."""

    def __init__(self):
        super().__init__(name="Do-Nothing Baseline")

    def act(self, observation: Any, legal_actions: Optional[List[Any]] = None) -> ActionProposal:
        return ActionProposal(
            action_type=ActionType.NOOP,
            rationale="Passively monitor grid state without intervention."
        )
