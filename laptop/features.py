# laptop/features.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np


def _ema(prev: float, x: float, alpha: float) -> float:
    return alpha * prev + (1.0 - alpha) * x


def _deadzone(x: float, dz: float, center: float = 0.0) -> float:
    d = x - center
    if abs(d) < dz:
        return center
    return x


@dataclass
class FeatureState:
    wrist_x: float = 0.5
    wrist_y: float = 0.5
    index_mcp_y: float = 0.5
    pinch: float = 0.3
    roll: float = 0.5


class FeatureExtractor:
    """
    v1 features from 2D landmarks (normalized):
    1) wrist_x, wrist_y (landmark 0)
    2) index_mcp_y (landmark 5) helps with wrist pitch mapping
    3) pinch distance between thumb tip (4) and index tip (8)
    4) roll proxy using relative x of index_mcp (5) vs pinky_mcp (17)
    """

    def __init__(self, ema_alpha: float, dz_wrist_xy: float, dz_roll: float, dz_pinch: float) -> None:
        self.alpha = float(ema_alpha)
        self.dz_wrist_xy = float(dz_wrist_xy)
        self.dz_roll = float(dz_roll)
        self.dz_pinch = float(dz_pinch)
        self.state = FeatureState()

    def extract(self, landmarks: np.ndarray) -> Dict[str, float]:
        # landmarks: (21,3), x/y normalized
        wrist = landmarks[0]
        index_mcp = landmarks[5]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        pinky_mcp = landmarks[17]

        wrist_x = float(wrist[0])
        wrist_y = float(wrist[1])
        index_mcp_y = float(index_mcp[1])

        pinch = float(np.linalg.norm((thumb_tip[:2] - index_tip[:2])))
        # normalize pinch somewhat (typical range ~0.02..0.25). clamp to [0..1]
        pinch_n = float(np.clip((pinch - 0.02) / 0.23, 0.0, 1.0))

        # roll proxy: compare knuckle x positions. Map to [0..1]
        roll_raw = float(np.clip((index_mcp[0] - pinky_mcp[0]) * 2.0 + 0.5, 0.0, 1.0))

        # Deadzones around neutral
        wrist_x = _deadzone(wrist_x, self.dz_wrist_xy, center=0.5)
        wrist_y = _deadzone(wrist_y, self.dz_wrist_xy, center=0.5)
        index_mcp_y = _deadzone(index_mcp_y, self.dz_wrist_xy, center=0.5)
        roll_raw = _deadzone(roll_raw, self.dz_roll, center=0.5)
        pinch_n = _deadzone(pinch_n, self.dz_pinch, center=self.state.pinch)  # reduce micro jitter

        # EMA smoothing
        s = self.state
        s.wrist_x = _ema(s.wrist_x, wrist_x, self.alpha)
        s.wrist_y = _ema(s.wrist_y, wrist_y, self.alpha)
        s.index_mcp_y = _ema(s.index_mcp_y, index_mcp_y, self.alpha)
        s.pinch = _ema(s.pinch, pinch_n, self.alpha)
        s.roll = _ema(s.roll, roll_raw, self.alpha)

        return {
            "wrist_x": s.wrist_x,
            "wrist_y": s.wrist_y,
            "index_mcp_y": s.index_mcp_y,
            "pinch": s.pinch,
            "roll": s.roll,
        }
