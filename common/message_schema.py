# common/message_schema.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


@dataclass
class TeleopCommand:
    seq: int
    ts: float          # sender wall timestamp (seconds)
    confidence: float
    estop: bool
    torque: bool
    joints: Dict[int, int]  # motor_id -> goal_position ticks
    features: Dict[str, float]  # wrist_x, wrist_y, pinch, roll, etc.


def validate_cmd(msg: Dict[str, Any]) -> Tuple[bool, str]:
    required = ["type", "seq", "ts", "confidence", "estop", "torque", "joints", "features"]
    for k in required:
        if k not in msg:
            return False, f"Missing key: {k}"
    if msg["type"] != "cmd":
        return False, "type must be 'cmd'"

    try:
        seq = int(msg["seq"])
        if seq < 0:
            return False, "seq must be >= 0"
        float(msg["ts"])
        conf = float(msg["confidence"])
        if not (0.0 <= conf <= 1.0):
            return False, "confidence must be in [0,1]"
        bool(msg["estop"])
        bool(msg["torque"])

        joints = msg["joints"]
        if not isinstance(joints, dict):
            return False, "joints must be a dict"
        for k, v in joints.items():
            mid = int(k)
            if mid < 1 or mid > 253:
                return False, f"Invalid motor id: {mid}"
            int(v)

        feats = msg["features"]
        if not isinstance(feats, dict):
            return False, "features must be a dict"
        for fk, fv in feats.items():
            _ = str(fk)
            float(fv)
    except Exception as e:
        return False, f"Type conversion error: {e}"

    return True, "ok"


def to_command(msg: Dict[str, Any]) -> TeleopCommand:
    joints = {int(k): int(v) for k, v in msg["joints"].items()}
    feats = {str(k): float(v) for k, v in msg["features"].items()}
    return TeleopCommand(
        seq=int(msg["seq"]),
        ts=float(msg["ts"]),
        confidence=float(msg["confidence"]),
        estop=bool(msg["estop"]),
        torque=bool(msg["torque"]),
        joints=joints,
        features=feats,
    )
