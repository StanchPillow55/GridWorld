import pytest
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter
from backend.app.schemas import ActionProposal, ActionType


@pytest.fixture(scope="module")
def adapter():
    ad = Grid2OpAdapter("l2rpn_case14_sandbox")
    yield ad
    ad.close()


def test_valid_noop_action(adapter):
    proposal = ActionProposal(action_type=ActionType.NOOP)
    action, is_valid = adapter.create_grid2op_action(proposal)
    assert is_valid is True
    assert action is not None


def test_valid_switch_line_action(adapter):
    proposal = ActionProposal(action_type=ActionType.SWITCH_LINE, target_id=0)
    action, is_valid = adapter.create_grid2op_action(proposal)
    assert is_valid is True
    assert action is not None


def test_invalid_line_id(adapter):
    # Line 999 does not exist in 20-line IEEE-14
    proposal = ActionProposal(action_type=ActionType.SWITCH_LINE, target_id=999)
    action, is_valid = adapter.create_grid2op_action(proposal)
    assert is_valid is False
