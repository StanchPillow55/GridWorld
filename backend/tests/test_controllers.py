import pytest
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter
from backend.app.controllers.noop import NoopController
from backend.app.controllers.simple_heuristic import SimpleHeuristicController
from backend.app.controllers.simulation_planner import SimulationGuidedPlanner
from backend.app.controllers.direct_llm import DirectLLMController
from backend.app.controllers.refinement_llm import RefinementLLMController
from backend.app.schemas import ActionType


@pytest.fixture(scope="module")
def adapter():
    ad = Grid2OpAdapter("l2rpn_case14_sandbox")
    yield ad
    ad.close()


def test_controller_separation_and_budgets(adapter):
    obs = adapter.reset_chronic(chronic_id=3, seed=42)
    candidates = adapter.get_candidate_actions(obs, max_candidates=6)

    # 1. Noop Controller
    noop = NoopController()
    p_noop, rounds_noop = noop.act(obs, candidates, adapter)
    assert p_noop.action_type == ActionType.NOOP
    assert noop.resource_usage.simulation_calls == 0
    assert noop.resource_usage.model_calls == 0

    # 2. Simple Heuristic (Strictly 0 simulation calls)
    heur = SimpleHeuristicController()
    p_heur, rounds_heur = heur.act(obs, candidates, adapter)
    assert heur.resource_usage.simulation_calls == 0
    assert heur.resource_usage.model_calls == 0

    # 3. Simulation-Guided Planner (uses simulation calls up to forecast budget)
    planner = SimulationGuidedPlanner(forecast_budget=4)
    p_plan, rounds_plan = planner.act(obs, candidates, adapter)
    assert planner.resource_usage.simulation_calls <= 4
    assert len(rounds_plan) <= 4
    assert any(r.selected for r in rounds_plan)

    # 4. Direct LLM in offline mode -> must label fallback_used = True
    direct_llm = DirectLLMController(api_key=None, ollama_url="http://invalid-host:9999")
    p_direct, _ = direct_llm.act(obs, candidates, adapter)
    assert direct_llm.fallback_used is True
    assert direct_llm.resource_usage.simulation_calls == 0

    # 5. Refinement LLM in offline mode -> produces multi-round refinement records
    refine_llm = RefinementLLMController(api_key=None, ollama_url="http://invalid-host:9999", max_rounds=3)
    p_refine, rounds_refine = refine_llm.act(obs, candidates, adapter)
    assert refine_llm.fallback_used is True  # correctly labeled as fallback!
    assert len(rounds_refine) >= 1
    assert refine_llm.resource_usage.simulation_calls >= 1
    assert any(r.selected for r in rounds_refine)
