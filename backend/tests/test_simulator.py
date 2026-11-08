import pytest
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter
from backend.app.schemas import GridTopology, ActionProposal, ActionType


@pytest.fixture(scope="module")
def adapter():
    ad = Grid2OpAdapter("l2rpn_case14_sandbox")
    yield ad
    ad.close()


def test_topology_extraction(adapter):
    topo = adapter.get_topology()
    assert isinstance(topo, GridTopology)
    assert topo.n_sub == 14
    assert topo.n_line == 20
    assert topo.n_gen == 6
    assert topo.n_load == 11
    assert len(topo.substations) == 14
    assert len(topo.lines) == 20
    assert len(topo.generators) == 6
    assert len(topo.loads) == 11

    # Verify positions exist for React Flow rendering
    for sub in topo.substations:
        assert sub.pos_x > 0
        assert sub.pos_y > 0


def test_simulation_step(adapter):
    env = adapter.env
    obs = env.reset()
    action, valid = adapter.create_grid2op_action(ActionProposal(action_type=ActionType.NOOP))
    assert valid is True

    next_obs, reward, done, info = env.step(action)
    step = adapter.observation_to_step(
        obs=next_obs,
        step_idx=1,
        action_taken=ActionProposal(action_type=ActionType.NOOP),
        reward=reward,
        done=done
    )

    assert step.step == 1
    assert step.max_rho >= 0.0
    assert len(step.line_rhos) == 20
    assert len(step.line_status) == 20
    assert step.total_load_mw > 0
    assert step.total_gen_mw > 0
