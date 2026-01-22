# laptop/mapping.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from common.config import JointCalib


@dataclass
class MapRule:
    feature: str
    feature_center: float
    gain: float
    invert: bool


class HandToJointMapper:
    def __init__(self, mapping_cfg: Dict, calib: Dict[int, JointCalib]) -> None:
        self.calib = calib
        self.margin = int(mapping_cfg.get("soft_limit_margin_ticks", 0))

        m = mapping_cfg["mapping"]
        self.rules: Dict[int, MapRule] = {
            1: MapRule(**m["joint_1_base_yaw"]),
            2: MapRule(**m["joint_2_shoulder"]),
            3: MapRule(**m["joint_3_elbow"]),
            4: MapRule(**m["joint_4_wrist_pitch"]),
            5: MapRule(**m["joint_5_wrist_roll"]),
            6: MapRule(**m["joint_6_gripper"]),
        }

    def _clamp(self, mid: int, val: int) -> int:
        c = self.calib[mid]
        lo = c.range_min + self.margin
        hi = c.range_max - self.margin
        if lo > hi:
            lo, hi = c.range_min, c.range_max
        return max(lo, min(hi, val))

    def map(self, features: Dict[str, float]) -> Dict[int, int]:
        out: Dict[int, int] = {}
        for mid, rule in self.rules.items():
            c = self.calib[mid]
            center = (c.range_min + c.range_max) / 2.0
            span = (c.range_max - c.range_min) / 2.0

            f = float(features.get(rule.feature, rule.feature_center))
            # normalized delta in [-1..+1] roughly
            d = (f - rule.feature_center) * 2.0
            d = max(-1.0, min(1.0, d))

            if rule.invert:
                d = -d

            target = int(round(center + span * rule.gain * d))
            out[mid] = self._clamp(mid, target)

        return out
