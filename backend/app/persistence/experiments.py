import os
import json
from pathlib import Path
from typing import List, Optional
from backend.app.schemas import ExperimentRecord, ReplayData

EXPERIMENTS_DIR = Path("experiments")
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)


def save_experiment_record(record: ExperimentRecord, replay: Optional[ReplayData] = None) -> str:
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = EXPERIMENTS_DIR / f"{record.id}_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(record.model_dump_json(indent=2))

    if replay:
        replay_path = EXPERIMENTS_DIR / f"{record.id}_replay.json"
        with open(replay_path, "w", encoding="utf-8") as f:
            f.write(replay.model_dump_json(indent=2))

    return record.id


def get_experiment_record(experiment_id: str) -> Optional[ExperimentRecord]:
    summary_path = EXPERIMENTS_DIR / f"{experiment_id}_summary.json"
    if not summary_path.exists():
        return None
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return ExperimentRecord.model_validate(data)


def get_experiment_replay(experiment_id: str) -> Optional[ReplayData]:
    replay_path = EXPERIMENTS_DIR / f"{experiment_id}_replay.json"
    if not replay_path.exists():
        return None
    with open(replay_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return ReplayData.model_validate(data)


def list_experiment_records() -> List[ExperimentRecord]:
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for file in sorted(EXPERIMENTS_DIR.glob("*_summary.json"), key=os.path.getmtime, reverse=True):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                records.append(ExperimentRecord.model_validate(data))
        except Exception:
            continue
    return records
