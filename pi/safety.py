# pi/safety.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from common.config import JointCalib
from common.timeutil import now_s


@dataclass
class SafetyState:
    estop: bool = False
    torque: bool = True
    last_good_cmd_mono_s: float = 0.0
    last_cmd_seq: int = -1


class SafetyLayer:
    def __init__(
        self,
        calib: Dict[int, JointCalib],
        stale_timeout_s: float,
        hard_stop_timeout_s: float,
    ) -> None:
        self.calib = calib
        self.stale_timeout_s = float(stale_timeout_s)
        self.hard_stop_timeout_s = float(hard_stop_timeout_s)
        self.state = SafetyState(last_good_cmd_mono_s=now_s())
        self.home_pose: Dict[int, int] = {
            mid: int((c.range_min + c.range_max) / 2) for mid, c in calib.items()
        }

    def set_home_pose(self, pose: Dict[int, int]) -> None:
        self.home_pose = dict(pose)

    def clamp(self, joints: Dict[int, int]) -> Dict[int, int]:
        out: Dict[int, int] = {}
        for mid, val in joints.items():
            c = self.calib[mid]
            out[mid] = max(c.range_min, min(c.range_max, int(val)))
        return out

    def apply(self, seq: int, estop: bool, torque: bool, confidence_ok: bool, joints: Dict[int, int], home_req: bool):
        # Update global states from command
        self.state.estop = bool(estop)
        self.state.torque = bool(torque)

        # E-stop always wins
        if self.state.estop:
            return {
                "mode": "ESTOP",
                "torque": False,
                "joints": None,
            }

        # Home request (v1 uses a feature flag)
        if home_req:
            return {
                "mode": "HOME",
                "torque": self.state.torque,
                "joints": self.clamp(self.home_pose),
            }

        if confidence_ok:
            self.state.last_good_cmd_mono_s = now_s()
            self.state.last_cmd_seq = seq
            return {
                "mode": "TRACK",
                "torque": self.state.torque,
                "joints": self.clamp(joints),
            }

        # If confidence not OK, we don't “invent” motion.
        # We hold last commanded pose in driver layer by simply not updating.
        return {
            "mode": "LOW_CONF",
            "torque": self.state.torque,
            "joints": None,
        }

    def stale_policy(self):
        age = now_s() - self.state.last_good_cmd_mono_s
        if age > self.hard_stop_timeout_s:
            return "HARD_STOP"
        if age > self.stale_timeout_s:
            return "SOFT_HOLD"
        return "OK"
