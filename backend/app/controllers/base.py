from abc import ABC, abstractmethod
from typing import Any, List, Optional
from backend.app.schemas import ActionProposal


class BaseController(ABC):
    """Abstract base class for all GridWorld controllers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def act(self, observation: Any, legal_actions: Optional[List[Any]] = None) -> ActionProposal:
        """Given a Grid2Op observation, return an ActionProposal."""
        pass

    def reset(self):
        """Reset internal controller state before a new episode."""
        pass
