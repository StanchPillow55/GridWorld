import pytest
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter
from backend.app.schemas import ActionProposal, ActionType


@pytest.fixture(scope="module")
def adapter():
    ad = Grid2OpAdapter("l2rpn_case14_sandbox")
    yield ad
    ad.close()


def test_candidate_catalog_generation(adapter):
    obs = adapter.reset_chronic(chronic_id=3, seed=42)
    candidates = adapter.get_candidate_actions(obs, max_candidates=8)

    assert len(candidates) >= 2
    # First action must always be NOOP (A0)
    assert candidates[0].action_id == "A0"
    assert candidates[0].action_type == ActionType.NOOP

    # Subsequent actions must be valid candidate actions with descriptions
    for c in candidates[1:]:
        assert c.action_id.startswith("A")
        assert len(c.description) > 5


def test_valid_and_invalid_action_conversion(adapter):
    # Valid NOOP
    proposal = ActionProposal(action_type=ActionType.NOOP)
    action, is_valid = adapter.create_grid2op_action(proposal)
    assert is_valid is True
    assert action is not None

    # Valid switch line
    proposal = ActionProposal(action_type=ActionType.SWITCH_LINE, target_id=7)
    action, is_valid = adapter.create_grid2op_action(proposal)
    assert is_valid is True

    # Invalid line ID (out of bounds)
    proposal_invalid = ActionProposal(action_type=ActionType.SWITCH_LINE, target_id=999)
    _, is_valid = adapter.create_grid2op_action(proposal_invalid)
    assert is_valid is False
