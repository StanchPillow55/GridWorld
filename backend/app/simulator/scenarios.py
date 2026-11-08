from typing import Dict, List
from backend.app.schemas import ScenarioConfig, ScenarioDisturbance

DEFAULT_SCENARIOS: Dict[str, ScenarioConfig] = {
    "case14_normal": ScenarioConfig(
        id="case14_normal",
        name="IEEE-14 Normal Operation",
        description="Standard 14-bus test case under typical load variations with no forced outages.",
        env_name="l2rpn_case14_sandbox",
        seed=42,
        max_steps=30,
        disturbances=[]
    ),
    "case14_corridor_congest": ScenarioConfig(
        id="case14_corridor_congest",
        name="Transmission Corridor Disruption",
        description="Forced outage of transmission line 1 at step 4, inducing heavy rerouted power flows across lines 2 and 4.",
        env_name="l2rpn_case14_sandbox",
        seed=101,
        max_steps=30,
        disturbances=[
            ScenarioDisturbance(step=4, line_id=1, action="disconnect")
        ]
    ),
    "case14_cascade_stress": ScenarioConfig(
        id="case14_cascade_stress",
        name="Severe Multi-Line Stress Test",
        description="Sequential line disconnects simulating storm/fire damage at steps 3 and 8 to test cascade prevention.",
        env_name="l2rpn_case14_sandbox",
        seed=2024,
        max_steps=35,
        disturbances=[
            ScenarioDisturbance(step=3, line_id=2, action="disconnect"),
            ScenarioDisturbance(step=8, line_id=4, action="disconnect")
        ]
    )
}


def get_scenario(scenario_id: str) -> ScenarioConfig:
    if scenario_id in DEFAULT_SCENARIOS:
        return DEFAULT_SCENARIOS[scenario_id]
    raise ValueError(f"Unknown scenario ID: {scenario_id}")


def list_scenarios() -> List[ScenarioConfig]:
    return list(DEFAULT_SCENARIOS.values())
