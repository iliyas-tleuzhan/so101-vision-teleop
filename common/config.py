# common/config.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def load_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


@dataclass
class JointCalib:
    motor_id: int
    range_min: int
    range_max: int
    homing_offset: int


def load_calibration(calib_path: str | Path) -> Dict[int, JointCalib]:
    data = load_json(calib_path)
    # Accept either:
    # 1) {"joints":[{"motor_id":1,"range_min":...}, ...]}
    # 2) {"1":{"range_min":...}, "2":{...}}
    joints: Dict[int, JointCalib] = {}

    if isinstance(data, dict) and "joints" in data and isinstance(data["joints"], list):
        for j in data["joints"]:
            mid = int(j["motor_id"])
            joints[mid] = JointCalib(
                motor_id=mid,
                range_min=int(j["range_min"]),
                range_max=int(j["range_max"]),
                homing_offset=int(j.get("homing_offset", 0)),
            )
    elif isinstance(data, dict):
        for k, v in data.items():
            try:
                mid = int(k)
                joints[mid] = JointCalib(
                    motor_id=mid,
                    range_min=int(v["range_min"]),
                    range_max=int(v["range_max"]),
                    homing_offset=int(v.get("homing_offset", 0)),
                )
            except Exception:
                continue
    else:
        raise ValueError(f"Unsupported calibration JSON format: {calib_path}")

    # Basic sanity check for IDs 1–6
    for mid in range(1, 7):
        if mid not in joints:
            raise ValueError(f"Calibration missing motor_id {mid}. Found: {sorted(joints.keys())}")

    return joints
