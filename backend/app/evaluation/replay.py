import logging
from typing import List, Optional, Tuple
import numpy as np

from backend.app.schemas import (
    ReplayData,
    StepObservation,
    ExperimentMetrics,
    GridTopology,
    ControllerType,
    ProvenanceMetadata,
    ActionType
)
from backend.app.simulator.grid2op_adapter import Grid2OpAdapter

logger = logging.getLogger(__name__)


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


def reproduce_trajectory_in_fresh_env(replay: ReplayData) -> Tuple[bool, float]:
    """
    Independently verify trajectory by re-executing recorded actions
    in a freshly instantiated Grid2Op environment without reading saved observations.
    Returns (is_reproducible, max_numerical_divergence).
    """
    fresh_adapter = Grid2OpAdapter(replay.provenance.env_name)
    env = fresh_adapter.env

    obs = fresh_adapter.reset_chronic(
        chronic_id=replay.provenance.chronic_id,
        seed=replay.provenance.seed
    )

    max_divergence = 0.0

    # Step 0 comparison
    initial_recorded_rho = replay.steps[0].max_rho
    initial_fresh_rho = float(np.max(obs.rho))
    diff_0 = abs(initial_fresh_rho - initial_recorded_rho)
    if diff_0 > max_divergence:
        max_divergence = diff_0

    for step in replay.steps[1:]:
        # Convert recorded action proposal to Grid2Op action
        action, is_valid = fresh_adapter.create_grid2op_action(step.action_taken)
        obs, reward, done, info = env.step(action)

        fresh_max_rho = float(np.max(obs.rho)) if len(obs.rho) > 0 else 0.0
        diff = abs(fresh_max_rho - step.max_rho)
        if diff > max_divergence:
            max_divergence = diff

        # If divergence exceeds machine precision, reproduction fails
        if diff > 1e-3:
            fresh_adapter.close()
            return False, max_divergence

        if done:
            break

    fresh_adapter.close()
    return True, max_divergence
