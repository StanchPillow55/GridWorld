export type ControllerType = 'noop' | 'heuristic' | 'ai';
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
}

export interface ActionProposal {
  action_type: ActionType;
  target_id?: number | null;
  target_bus?: number | null;
  redispatch_val?: number | null;
  rationale?: string;
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
  reward: number;
  done: boolean;
  done_reason?: string | null;
}

export interface ScenarioDisturbance {
  step: number;
  line_id: number;
  action: string;
}

export interface ScenarioConfig {
  id: string;
  name: string;
  description: string;
  env_name: string;
  seed: number;
  max_steps: number;
  disturbances: ScenarioDisturbance[];
}

export interface ExperimentMetrics {
  survival_steps: number;
  max_steps: number;
  survived: boolean;
  peak_line_utilization: number;
  mean_line_utilization: number;
  overload_violations: number;
  actions_taken: number;
  invalid_actions: number;
  execution_time_ms: number;
}

export interface ExperimentRecord {
  id: string;
  scenario_id: string;
  controller_type: ControllerType;
  timestamp: string;
  metrics: ExperimentMetrics;
  actions_summary: string[];
}

export interface ReplayData {
  experiment_id: string;
  scenario_id: string;
  controller_type: ControllerType;
  topology: GridTopology;
  metrics: ExperimentMetrics;
  steps: StepObservation[];
}
