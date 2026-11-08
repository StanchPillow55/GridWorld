from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import (
    GridTopology,
    ScenarioConfig,
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
    title="GridWorld API",
    description="Autonomous power-grid resilience, control experimentation, and evaluation engine",
    version="0.1.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared adapter and runner instances
adapter = Grid2OpAdapter()
runner = ExperimentRunner(adapter=adapter)


@app.get("/api/environment", response_model=GridTopology)
def get_environment_topology():
    """Retrieve electrical network topology (substations, lines, generators, loads)."""
    return adapter.get_topology()


@app.get("/api/scenarios", response_model=List[ScenarioConfig])
def get_scenarios():
    """List all available benchmark scenarios."""
    return list_scenarios()


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
    """Retrieve an experiment record summary."""
    rec = get_experiment_record(experiment_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return rec


@app.get("/api/experiments/{experiment_id}/replay", response_model=ReplayData)
def get_experiment_replay_data(experiment_id: str):
    """Retrieve step-by-step replay trajectory for animation and detailed inspection."""
    rep = get_experiment_replay(experiment_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Replay data not found for this experiment")
    return rep


@app.post("/api/benchmark", response_model=List[ExperimentRecord])
def run_head_to_head_benchmark(scenario_id: str = "case14_corridor_congest", max_steps: int = 25):
    """Run head-to-head comparison across Do-Nothing, Heuristic, and AI controllers on the same scenario."""
    controllers = [ControllerType.NOOP, ControllerType.HEURISTIC, ControllerType.AI]
    results = []
    for ctrl in controllers:
        req = ExperimentRunRequest(
            scenario_id=scenario_id,
            controller_type=ctrl,
            max_steps=max_steps
        )
        record, _ = runner.run_experiment(req)
        results.append(record)
    return results


@app.get("/health")
def health_check():
    return {"status": "ok", "env": adapter.env_name, "version": "0.1.0"}
