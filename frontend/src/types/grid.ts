export type ControllerType =
  | 'noop'
  | 'simple_heuristic'
  | 'simulation_planner'
  | 'direct_llm'
  | 'refinement_llm';

export type ActionType = 'noop' | 'switch_line' | 'change_bus' | 'redispatch';

export interface SubstationInfo {
  id: number;
  name: string;
  pos_x: number;
  pos_y: number;
  connected_lines: number[];
  generators: number[];
  loads: number[];
}

export interface LineInfo {
  id: number;
  name: string;
  from_sub: number;
  to_sub: number;
  thermal_limit: number;
  rho: number;
  status: boolean;
  p_or: number;
  q_or: number;
}

export interface GeneratorInfo {
  id: number;
  name: string;
  sub_id: number;
  p: number;
  p_min: number;
  p_max: number;
}

export interface LoadInfo {
  id: number;
  name: string;
  sub_id: number;
  p: number;
  q: number;
}

export interface GridTopology {
  name: string;
  n_sub: number;
  n_line: number;
  n_gen: number;
  n_load: number;
  substations: SubstationInfo[];
  lines: LineInfo[];
  generators: GeneratorInfo[];
  loads: LoadInfo[];
  busbar_modeling_note?: string;
}

export interface CandidateAction {
  action_id: string;
  action_type: ActionType;
  target_id?: number | null;
  target_bus?: number | null;
  redispatch_val?: number | null;
  description: string;
}

export interface ActionProposal {
  action_id?: string;
  action_type: ActionType;
  target_id?: number | null;
  target_bus?: number | null;
  redispatch_val?: number | null;
  rationale?: string;
}

export interface ProposalRoundRecord {
  round_index: number;
  action_id: string;
  action_type: ActionType;
  target_id?: number | null;
  rationale: string;
  simulated_max_rho: number;
  simulated_done: boolean;
  feedback: string;
  selected: boolean;
}

export interface ForecastVerification {
  forecasted_max_rho: number;
  actual_max_rho: number;
  forecast_error: number;
}

export interface StepObservation {
  step: number;
  max_rho: number;
  mean_rho: number;
  line_rhos: number[];
  line_status: boolean[];
  total_load_mw: number;
  total_gen_mw: number;
  action_taken: ActionProposal;
  proposals_history?: ProposalRoundRecord[];
  forecast_verification?: ForecastVerification | null;
  reward: number;
  done: boolean;
  done_reason?: string | null;
  fallback_used?: boolean;
}

export interface ScenarioDisturbance {
  step: number;
  line_id: number;
  action: string;
}

export type ScenarioSplit = 'dev' | 'held_out';

export interface ScenarioConfig {
  id: string;
  name: string;
  description: string;
  split: ScenarioSplit;
  env_name: string;
  chronic_id: number;
  start_step: number;
  seed: number;
  max_steps: number;
  disturbances: ScenarioDisturbance[];
}

export interface ProvenanceMetadata {
  timestamp_utc: string;
  python_version: string;
  grid2op_version: string;
  backend_class: string;
  platform: string;
  env_name: string;
  chronic_subpath: string;
  chronic_id: number;
  start_step: number;
  seed: number;
  max_steps: number;
  disturbances: ScenarioDisturbance[];
}

export interface ResourceUsage {
  simulation_calls: number;
  model_calls: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  model_latency_ms: number;
  estimated_cost_usd: number;
}

export interface ExperimentMetrics {
  survival_steps: number;
  max_steps: number;
  survived: boolean;
  hard_failure: boolean;
  peak_line_utilization: number;
  mean_line_utilization: number;
  overload_violations: number;
  overload_severity: number;
  actions_taken: number;
  invalid_actions: number;
  forecast_mean_absolute_error: number;
  execution_time_ms: number;
  resource_usage: ResourceUsage;
  fallback_used: boolean;
}

export interface ExperimentRecord {
  id: string;
  scenario_id: string;
  controller_type: ControllerType;
  timestamp: string;
  provenance: ProvenanceMetadata;
  metrics: ExperimentMetrics;
  actions_summary: string[];
}

export interface ReplayData {
  experiment_id: string;
  scenario_id: string;
  controller_type: ControllerType;
  provenance: ProvenanceMetadata;
  topology: GridTopology;
  metrics: ExperimentMetrics;
  steps: StepObservation[];
}
