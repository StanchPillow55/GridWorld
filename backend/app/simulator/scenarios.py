from typing import Dict, List
from backend.app.schemas import ScenarioConfig, ScenarioDisturbance, ScenarioSplit

BENCHMARK_SCENARIOS: Dict[str, ScenarioConfig] = {
    # --- DEVELOPMENT SPLIT ---
    "dev_chronic_0003_overload": ScenarioConfig(
        id="dev_chronic_0003_overload",
        name="[DEV] Severe Chronic 0003 Overload (Cascade Threat)",
        description="Authentic Grid2Op chronic where Line 17 experiences natural severe thermal overload (rho=1.028) at initialization. Baseline Do-Nothing trips on thermal protection after 2 steps and triggers complete network divergence/blackout. Active control can reconfigure topology to prevent blackout.",
        split=ScenarioSplit.DEV,
        env_name="l2rpn_case14_sandbox",
        chronic_id=3,
        start_step=0,
        seed=42,
        max_steps=25,
        disturbances=[]
    ),
    "dev_chronic_0001_congest": ScenarioConfig(
        id="dev_chronic_0001_congest",
        name="[DEV] Chronic 0001 Heavy Transmission Loading",
        description="High demand profile in chronic 0001 driving peak line loading up to 93% across parallel lines 1 and 3. Tests proactive thermal relief.",
        split=ScenarioSplit.DEV,
        env_name="l2rpn_case14_sandbox",
        chronic_id=1,
        start_step=0,
        seed=101,
        max_steps=30,
        disturbances=[]
    ),

    # --- HELD-OUT EVALUATION SPLIT ---
    "heldout_chronic_0000_normal": ScenarioConfig(
        id="heldout_chronic_0000_normal",
        name="[HELD-OUT] Chronic 0000 Normal Operation",
        description="Unseen chronic with nominal loading (< 81%). Evaluates controller stability and penalizes unnecessary switching.",
        split=ScenarioSplit.HELD_OUT,
        env_name="l2rpn_case14_sandbox",
        chronic_id=0,
        start_step=0,
        seed=2024,
        max_steps=30,
        disturbances=[]
    ),
    "heldout_chronic_0002_corridor": ScenarioConfig(
        id="heldout_chronic_0002_corridor",
        name="[HELD-OUT] Chronic 0002 Forced Corridor Outage",
        description="Unseen chronic combined with forced transmission corridor line 1 outage at step 4. Evaluates generalization under compound disturbances.",
        split=ScenarioSplit.HELD_OUT,
        env_name="l2rpn_case14_sandbox",
        chronic_id=2,
        start_step=0,
        seed=999,
        max_steps=30,
        disturbances=[
            ScenarioDisturbance(step=4, line_id=1, action="disconnect")
        ]
    )
}


def get_scenario(scenario_id: str) -> ScenarioConfig:
    if scenario_id in BENCHMARK_SCENARIOS:
        return BENCHMARK_SCENARIOS[scenario_id]
    raise ValueError(f"Unknown scenario ID: {scenario_id}")


def list_scenarios(split: str = None) -> List[ScenarioConfig]:
    scenarios = list(BENCHMARK_SCENARIOS.values())
    if split:
        return [s for s in scenarios if s.split.value == split]
    return scenarios
