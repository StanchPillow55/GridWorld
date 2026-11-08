import pytest
import numpy as np
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
    assert "busbar" in topo.busbar_modeling_note.lower()

    for sub in topo.substations:
        assert sub.pos_x > 0
        assert sub.pos_y > 0


def test_chronic_determinism(adapter):
    # Verify that resetting to chronic 3 with fixed seed produces identical initial state
    obs1 = adapter.reset_chronic(chronic_id=3, seed=42)
    rho1 = np.copy(obs1.rho)

    obs2 = adapter.reset_chronic(chronic_id=3, seed=42)
    rho2 = np.copy(obs2.rho)

    np.testing.assert_allclose(rho1, rho2, rtol=1e-5)
    # Line 17 initializes in severe thermal overload (> 1.0)
    assert obs1.rho[17] > 1.0


def test_provenance_metadata(adapter):
    adapter.reset_chronic(chronic_id=3, seed=42)
    provenance = adapter.get_provenance_metadata(max_steps=20, disturbances=[])
    assert provenance.chronic_id == 3
    assert provenance.seed == 42
    assert provenance.grid2op_version is not None
    assert provenance.backend_class is not None
    assert provenance.python_version is not None
