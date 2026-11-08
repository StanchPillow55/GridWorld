# GridWorld: Autonomous Power Grid Resilience & Control Experimentation

GridWorld is an experimental platform for testing autonomous and simulation-guided agents on sequential electrical grid disruptions, control decisions, and resilience optimization.

Developed for the **SF × MIT Energy Hack**, GridWorld pairs realistic numerical power-flow simulation (**Grid2Op**, **pandapower**, and **LightSim2Grid**) with independent evaluation metrics, reproducible scenario suites, and an interactive React Flow topology visualizer.

---

## ⚡ Architecture Overview

```
GridWorld/
├── backend/
│   ├── app/
│   │   ├── simulator/       # Grid2Op environment wrapper & physical state serialization
│   │   ├── controllers/     # Baselines (Do-Nothing, Heuristic Overload Reliever, AI Adapter)
│   │   ├── evaluation/      # Independent evaluation metrics, head-to-head runner, deterministic replays
│   │   ├── persistence/     # Experiment runs and trajectory storage
│   │   ├── schemas.py       # Pydantic schemas for topology, actions, and metrics
│   │   └── main.py          # FastAPI REST orchestrator
│   └── tests/               # Test suites (physics, actions, evaluator, replay)
├── frontend/                # Interactive React + TypeScript + React Flow + Plotly dashboard
├── scenarios/               # Benchmark scenarios (development and held-out test sets)
└── experiments/             # Serialized experiment runs and replay trajectories
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+ (macOS Apple Silicon or Linux)
- Node.js 18+ and npm

### 1. Backend Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run tests to verify the simulator and evaluation engine:
```bash
pytest backend/tests
```

Launch the FastAPI orchestrator:
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```
Interactive API documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to explore grid topology, run scenarios, and replay agent decisions.

---

## 🧪 Scientific Evaluation Framework

GridWorld evaluates agents independently of their training rewards. Key evaluation criteria:
- **Survival Timesteps**: Duration the agent keeps the grid energized before blackouts or cascade failures.
- **Maximum Thermal Loading ($\rho_{max}$)**: Peak ratio of line current to thermal threshold ($I / I_{max}$).
- **Overload Violations**: Number of timesteps lines operate beyond emergency thermal ratings.
- **Topological Action Efficiency**: Proportion of purposeful reconfigurations vs redundant switching.
- **Proposal Validity**: Detection and penalty for invalid or unfeasible action requests.

---

## 📜 Benchmark Scenarios
- `case14_disruption_01`: Standard IEEE 14-bus test environment (`l2rpn_case14_sandbox`) with forced transmission corridor disconnects during peak demand.
- `case14_disruption_02`: Generator redispatch loss combined with high renewable volatility.
