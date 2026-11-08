from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ControllerType(str, Enum):
    NOOP = "noop"
    HEURISTIC = "heuristic"
    AI = "ai"


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


class ActionProposal(BaseModel):
    action_type: ActionType = ActionType.NOOP
    target_id: Optional[int] = None      # Line ID or Substation ID
    target_bus: Optional[int] = None     # 1 or 2 if changing bus
    redispatch_val: Optional[float] = None
    rationale: Optional[str] = "No action taken"


class StepObservation(BaseModel):
    step: int
    max_rho: float
    mean_rho: float
    line_rhos: List[float]
    line_status: List[bool]
    total_load_mw: float
    total_gen_mw: float
    action_taken: ActionProposal
    reward: float
    done: bool
    done_reason: Optional[str] = None


class ScenarioDisturbance(BaseModel):
    step: int
    line_id: int
    action: str = "disconnect"  # "disconnect" or "reconnect"


class ScenarioConfig(BaseModel):
    id: str
    name: str
    description: str
    env_name: str = "l2rpn_case14_sandbox"
    seed: int = 42
    max_steps: int = 50
    disturbances: List[ScenarioDisturbance] = Field(default_factory=list)


class ExperimentRunRequest(BaseModel):
    scenario_id: str
    controller_type: ControllerType = ControllerType.HEURISTIC
    seed: Optional[int] = None
    max_steps: Optional[int] = None


class ExperimentMetrics(BaseModel):
    survival_steps: int
    max_steps: int
    survived: bool
    peak_line_utilization: float
    mean_line_utilization: float
    overload_violations: int
    actions_taken: int
    invalid_actions: int
    execution_time_ms: float


class ExperimentRecord(BaseModel):
    id: str
    scenario_id: str
    controller_type: ControllerType
    timestamp: str
    metrics: ExperimentMetrics
    actions_summary: List[str] = Field(default_factory=list)


class ReplayData(BaseModel):
    experiment_id: str
    scenario_id: str
    controller_type: ControllerType
    topology: GridTopology
    metrics: ExperimentMetrics
    steps: List[StepObservation]
