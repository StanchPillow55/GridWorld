import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import grid2op
from grid2op.Action import BaseAction
from grid2op.Observation import BaseObservation

from backend.app.schemas import (
    GridTopology,
    SubstationInfo,
    LineInfo,
    GeneratorInfo,
    LoadInfo,
    StepObservation,
    ActionProposal,
    ActionType
)

logger = logging.getLogger(__name__)

# Canonical 2D layout coordinates for IEEE 14-bus substations for clear React Flow graph rendering
SUBSTATION_LAYOUT = {
    0: (100.0, 420.0),   # Sub 0 (Bus 1, Slack Gen)
    1: (260.0, 420.0),   # Sub 1 (Bus 2, Gen)
    2: (120.0, 260.0),   # Sub 2 (Bus 3, Gen)
    3: (300.0, 260.0),   # Sub 3 (Bus 4)
    4: (210.0, 330.0),   # Sub 4 (Bus 5)
    5: (480.0, 420.0),   # Sub 5 (Bus 6, Gen)
    6: (440.0, 300.0),   # Sub 6 (Bus 7)
    7: (520.0, 300.0),   # Sub 7 (Bus 8, Gen)
    8: (380.0, 180.0),   # Sub 8 (Bus 9)
    9: (490.0, 180.0),   # Sub 9 (Bus 10)
    10: (460.0, 90.0),   # Sub 10 (Bus 11)
    11: (600.0, 420.0),  # Sub 11 (Bus 12)
    12: (600.0, 300.0),  # Sub 12 (Bus 13)
    13: (560.0, 180.0),  # Sub 13 (Bus 14)
}


class Grid2OpAdapter:
    """Adapter bridging Grid2Op environment with structured GridWorld schemas."""

    def __init__(self, env_name: str = "l2rpn_case14_sandbox"):
        self.env_name = env_name
        self.env = grid2op.make(self.env_name)
        self._topology: Optional[GridTopology] = None

    def get_topology(self) -> GridTopology:
        if self._topology is not None:
            return self._topology

        env = self.env
        substations = []
        for sub_id in range(env.n_sub):
            x, y = SUBSTATION_LAYOUT.get(sub_id, (float(sub_id * 50), float(sub_id * 50)))
            or_lines = np.where(env.line_or_to_subid == sub_id)[0]
            ex_lines = np.where(env.line_ex_to_subid == sub_id)[0]
            connected_lines = [int(l) for l in np.unique(np.concatenate([or_lines, ex_lines]))]

            substations.append(
                SubstationInfo(
                    id=sub_id,
                    name=str(env.name_sub[sub_id]),
                    pos_x=x,
                    pos_y=y,
                    connected_lines=connected_lines,
                    generators=[int(g) for g in np.where(env.gen_to_subid == sub_id)[0]],
                    loads=[int(l) for l in np.where(env.load_to_subid == sub_id)[0]]
                )
            )

        lines = []
        thermal_limits = env.get_thermal_limit()
        for line_id in range(env.n_line):
            from_sub = int(env.line_or_to_subid[line_id])
            to_sub = int(env.line_ex_to_subid[line_id])
            lines.append(
                LineInfo(
                    id=line_id,
                    name=str(env.name_line[line_id]),
                    from_sub=from_sub,
                    to_sub=to_sub,
                    thermal_limit=float(thermal_limits[line_id]),
                    rho=0.0,
                    status=True
                )
            )

        generators = []
        for gen_id in range(env.n_gen):
            generators.append(
                GeneratorInfo(
                    id=gen_id,
                    name=str(env.name_gen[gen_id]),
                    sub_id=int(env.gen_to_subid[gen_id]),
                    p=float(env.gen_pmin[gen_id]) if hasattr(env, "gen_pmin") else 0.0,
                    p_min=float(env.gen_pmin[gen_id]) if hasattr(env, "gen_pmin") else 0.0,
                    p_max=float(env.gen_pmax[gen_id]) if hasattr(env, "gen_pmax") else 100.0
                )
            )

        loads = []
        for load_id in range(env.n_load):
            loads.append(
                LoadInfo(
                    id=load_id,
                    name=str(env.name_load[load_id]),
                    sub_id=int(env.load_to_subid[load_id]),
                    p=0.0,
                    q=0.0
                )
            )

        self._topology = GridTopology(
            name=self.env_name,
            n_sub=int(env.n_sub),
            n_line=int(env.n_line),
            n_gen=int(env.n_gen),
            n_load=int(env.n_load),
            substations=substations,
            lines=lines,
            generators=generators,
            loads=loads
        )
        return self._topology

    def create_grid2op_action(self, proposal: ActionProposal) -> Tuple[BaseAction, bool]:
        """Convert an ActionProposal into a Grid2Op Action. Returns (action, is_valid)."""
        action_space = self.env.action_space
        try:
            if proposal.action_type == ActionType.NOOP or proposal.target_id is None:
                return action_space(), True

            if proposal.action_type == ActionType.SWITCH_LINE:
                line_id = int(proposal.target_id)
                if 0 <= line_id < self.env.n_line:
                    return action_space({"change_line_status": [line_id]}), True

            if proposal.action_type == ActionType.CHANGE_BUS:
                sub_id = int(proposal.target_id)
                bus_id = int(proposal.target_bus or 1)
                if 0 <= sub_id < self.env.n_sub and bus_id in (1, 2):
                    return action_space({"set_bus": {"substations_id": [(sub_id, bus_id)]}}), True

            return action_space(), False
        except Exception as e:
            logger.warning(f"Error creating Grid2Op action: {e}")
            return action_space(), False

    def observation_to_step(
        self,
        obs: BaseObservation,
        step_idx: int,
        action_taken: ActionProposal,
        reward: float,
        done: bool,
        done_reason: Optional[str] = None
    ) -> StepObservation:
        rhos = [float(r) for r in obs.rho]
        statuses = [bool(s) for s in obs.line_status]

        return StepObservation(
            step=step_idx,
            max_rho=float(np.max(obs.rho)) if len(obs.rho) > 0 else 0.0,
            mean_rho=float(np.mean(obs.rho)) if len(obs.rho) > 0 else 0.0,
            line_rhos=rhos,
            line_status=statuses,
            total_load_mw=float(np.sum(obs.load_p)),
            total_gen_mw=float(np.sum(obs.prod_p)),
            action_taken=action_taken,
            reward=float(reward),
            done=done,
            done_reason=done_reason
        )

    def close(self):
        if self.env:
            self.env.close()
