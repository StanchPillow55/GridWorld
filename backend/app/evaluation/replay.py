from typing import List, Optional
from backend.app.schemas import (
    ReplayData,
    StepObservation,
    ExperimentMetrics,
    GridTopology,
    ControllerType,
    ProvenanceMetadata
)


def build_replay_data(
    experiment_id: str,
    scenario_id: str,
    controller_type: ControllerType,
    provenance: ProvenanceMetadata,
    topology: GridTopology,
    metrics: ExperimentMetrics,
    steps: List[StepObservation]
) -> ReplayData:
    return ReplayData(
        experiment_id=experiment_id,
        scenario_id=scenario_id,
        controller_type=controller_type,
        provenance=provenance,
        topology=topology,
        metrics=metrics,
        steps=steps
    )
