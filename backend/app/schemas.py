from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ControllerType(str, Enum):
    NOOP = "noop"
    SIMPLE_HEURISTIC = "simple_heuristic"
    SIMULATION_PLANNER = "simulation_planner"
    DIRECT_LLM = "direct_llm"
    REFINEMENT_LLM = "refinement_llm"


class ActionType(str, Enum):
    NOOP = "noop"
    SWITCH_LINE = "switch_line"
    CHANGE_BUS = "change_bus"
    REDISPATCH = "redispatch"


class SubstationInfo(BaseModel):
    id: int
    name: str
    pos_x: float = 0.0
    pos_y: float = 0.0
    connected_lines: List[int] = Field(default_factory=list)
    generators: List[int] = Field(default_factory=list)
    loads: List[int] = Field(default_factory=list)


class LineInfo(BaseModel):
    id: int
    name: str
    from_sub: int
    to_sub: int
    thermal_limit: float
    rho: float = 0.0
    status: bool = True  # True = connected, False = disconnected
    p_or: float = 0.0    # Active power origin (MW)
    q_or: float = 0.0    # Reactive power origin (MVAr)


class GeneratorInfo(BaseModel):
    id: int
    name: str
    sub_id: int
    p: float = 0.0
    p_min: float = 0.0
    p_max: float = 0.0


class LoadInfo(BaseModel):
    id: int
    name: str
    sub_id: int
    p: float = 0.0
    q: float = 0.0


class GridTopology(BaseModel):
    name: str
    n_sub: int
    n_line: int
    n_gen: int
    n_load: int
    substations: List[SubstationInfo]
    lines: List[LineInfo]
    generators: List[GeneratorInfo]
    loads: List[LoadInfo]
    busbar_modeling_note: str = "Topology is rendered at substation level; dynamic dual-busbar reconfigurations within substations are evaluated numerically by Grid2Op."


class CandidateAction(BaseModel):
    action_id: str                      # e.g., "A0", "A1"
    action_type: ActionType
    target_id: Optional[int] = None      # Line ID, Substation ID, or Gen ID
    target_bus: Optional[int] = None
    redispatch_val: Optional[float] = None
    description: str


class ActionProposal(BaseModel):
    action_id: Optional[str] = "A0"
    action_type: ActionType = ActionType.NOOP
    target_id: Optional[int] = None
    target_bus: Optional[int] = None
    redispatch_val: Optional[float] = None
    rationale: Optional[str] = "No action taken"


class ProposalRoundRecord(BaseModel):
    round_index: int                    # 1, 2, 3
    action_id: str
    action_type: ActionType
    target_id: Optional[int] = None
    rationale: str
    simulated_max_rho: float
    simulated_done: bool
    feedback: str
    selected: bool = False


class ForecastVerification(BaseModel):
    forecasted_max_rho: float
    actual_max_rho: float
    forecast_error: float               # abs(actual_max_rho - forecasted_max_rho)


class StepObservation(BaseModel):
    step: int
    max_rho: float
    mean_rho: float
    line_rhos: List[float]
    line_status: List[bool]
    total_load_mw: float
    total_gen_mw: float
    action_taken: ActionProposal
    proposals_history: List[ProposalRoundRecord] = Field(default_factory=list)
    forecast_verification: Optional[ForecastVerification] = None
    reward: float
    done: bool
    done_reason: Optional[str] = None
    fallback_used: bool = False


class ScenarioDisturbance(BaseModel):
    step: int
    line_id: int
    action: str = "disconnect"          # "disconnect" or "reconnect"


class ScenarioSplit(str, Enum):
    DEV = "dev"
    HELD_OUT = "held_out"


class ScenarioConfig(BaseModel):
    id: str
    name: str
    description: str
    split: ScenarioSplit = ScenarioSplit.DEV
    env_name: str = "l2rpn_case14_sandbox"
    chronic_id: int = 0
    start_step: int = 0
    seed: int = 42
    max_steps: int = 30
    disturbances: List[ScenarioDisturbance] = Field(default_factory=list)


class ExperimentRunRequest(BaseModel):
    scenario_id: str
    controller_type: ControllerType = ControllerType.REFINEMENT_LLM
    seed: Optional[int] = None
    max_steps: Optional[int] = None
    max_proposals_per_step: int = 3
    forecast_budget: int = 5


class ProvenanceMetadata(BaseModel):
    timestamp_utc: str
    python_version: str
    grid2op_version: str
    backend_class: str
    platform: str
    env_name: str
    chronic_subpath: str
    chronic_id: int
    start_step: int
    seed: int
    max_steps: int
    disturbances: List[ScenarioDisturbance]


class ResourceUsage(BaseModel):
    simulation_calls: int = 0
    model_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0


class ExperimentMetrics(BaseModel):
    survival_steps: int
    max_steps: int
    survived: bool
    hard_failure: bool
    peak_line_utilization: float
    mean_line_utilization: float
    overload_violations: int
    overload_severity: float            # integrated sum of (rho - 1.0)
    actions_taken: int
    invalid_actions: int
    forecast_mean_absolute_error: float
    execution_time_ms: float
    resource_usage: ResourceUsage
    fallback_used: bool


class ExperimentRecord(BaseModel):
    id: str
    scenario_id: str
    controller_type: ControllerType
    timestamp: str
    provenance: ProvenanceMetadata
    metrics: ExperimentMetrics
    actions_summary: List[str] = Field(default_factory=list)


class ReplayData(BaseModel):
    experiment_id: str
    scenario_id: str
    controller_type: ControllerType
    provenance: ProvenanceMetadata
    topology: GridTopology
    metrics: ExperimentMetrics
    steps: List[StepObservation]
