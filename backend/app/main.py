from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import (
    GridTopology,
    ScenarioConfig,
    ScenarioSplit,
    ExperimentRunRequest,
    ExperimentRecord,
    ReplayData,
    ControllerType
)
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter
from backend.app.simulator.scenarios import list_scenarios, get_scenario
from backend.app.evaluation.runner import ExperimentRunner
from backend.app.persistence.experiments import (
    list_experiment_records,
    get_experiment_record,
    get_experiment_replay
)

app = FastAPI(
    title="GridWorld Scientific API",
    description="Autonomous power-grid resilience, online simulation-guided LLM experimentation, and evaluation engine",
    version="0.2.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

adapter = Grid2OpAdapter()
runner = ExperimentRunner(adapter=adapter)


@app.get("/api/environment", response_model=GridTopology)
def get_environment_topology():
    """Retrieve electrical network topology (substations, lines, generators, loads) and modeling assumptions."""
    return adapter.get_topology()


@app.get("/api/scenarios", response_model=List[ScenarioConfig])
def get_scenarios(split: Optional[ScenarioSplit] = Query(None, description="Filter by split (dev or held_out)")):
    """List benchmark scenarios, optionally filtered by development or held-out evaluation splits."""
    return list_scenarios(split=split.value if split else None)


@app.get("/api/scenarios/{scenario_id}", response_model=ScenarioConfig)
def get_scenario_by_id(scenario_id: str):
    """Retrieve details of a single scenario."""
    try:
        return get_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/experiments", response_model=ExperimentRecord)
def run_experiment_endpoint(req: ExperimentRunRequest):
    """Run an experiment with a chosen controller and scenario."""
    try:
        record, _ = runner.run_experiment(req)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment execution failed: {str(e)}")


@app.get("/api/experiments", response_model=List[ExperimentRecord])
def list_experiments():
    """List historical experiment runs."""
    return list_experiment_records()


@app.get("/api/experiments/{experiment_id}", response_model=ExperimentRecord)
def get_experiment(experiment_id: str):
    """Retrieve an experiment record summary with full provenance metadata."""
    rec = get_experiment_record(experiment_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return rec


@app.get("/api/experiments/{experiment_id}/replay", response_model=ReplayData)
def get_experiment_replay_data(experiment_id: str):
    """Retrieve complete step-by-step replay trajectory including refinement traces and forecast verification."""
    rep = get_experiment_replay(experiment_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Replay data not found for this experiment")
    return rep


@app.post("/api/benchmark", response_model=List[ExperimentRecord])
def run_head_to_head_benchmark(
    scenario_id: str = "dev_chronic_0003_overload",
    max_steps: int = 15
):
    """
    Run head-to-head comparison across all 5 controllers:
    1. No-op Baseline
    2. Simple Deterministic Heuristic
    3. Deterministic Simulation-Guided Planner
    4. Direct LLM Controller (Single-shot)
    5. Simulation-Guided Refinement LLM Controller
    """
    controllers = [
        ControllerType.NOOP,
        ControllerType.SIMPLE_HEURISTIC,
        ControllerType.SIMULATION_PLANNER,
        ControllerType.DIRECT_LLM,
        ControllerType.REFINEMENT_LLM
    ]
    results = []
    for ctrl in controllers:
        req = ExperimentRunRequest(
            scenario_id=scenario_id,
            controller_type=ctrl,
            max_steps=max_steps,
            forecast_budget=5,
            max_proposals_per_step=3
        )
        record, _ = runner.run_experiment(req)
        results.append(record)
    return results


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "env": adapter.env_name,
        "backend": adapter.env.backend.__class__.__name__,
        "version": "0.2.0"
    }
