# pi/logger.py
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from common.timeutil import wall_time_s


@dataclass
class LogState:
    path: Path
    rows: int = 0


class CSVLogger:
    def __init__(self, out_dir: str = "logs") -> None:
        self.dir = Path(out_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state: Optional[LogState] = None
        self._fh = None
        self._writer = None

    def start(self) -> Path:
        ts = int(wall_time_s())
        path = self.dir / f"run_{ts}.csv"
        self._fh = path.open("w", newline="", encoding="utf-8")
        self.state = LogState(path=path)

        header = (
            ["wall_s", "seq", "confidence", "mode", "estop", "torque"]
            + ["wrist_x", "wrist_y", "index_mcp_y", "pinch", "roll", "home"]
            + [f"cmd_j{i}" for i in range(1, 7)]
            + [f"pos_j{i}" for i in range(1, 7)]
        )
        self._writer = csv.writer(self._fh)
        self._writer.writerow(header)
        self._fh.flush()
        return path

    def write(
        self,
        seq: int,
        confidence: float,
        mode: str,
        estop: bool,
        torque: bool,
        features: Dict[str, float],
        cmd: Dict[int, int],
        pos: Optional[Dict[int, int]],
    ) -> None:
        if not self._writer or not self.state:
            return
        row = [
            f"{wall_time_s():.6f}",
            int(seq),
            f"{float(confidence):.3f}",
            mode,
            int(bool(estop)),
            int(bool(torque)),
        ]
        for k in ["wrist_x", "wrist_y", "index_mcp_y", "pinch", "roll", "home"]:
            row.append(f"{float(features.get(k, 0.0)):.6f}")

        for i in range(1, 7):
            row.append(int(cmd.get(i, 0)))

        if pos is None:
            row.extend([0] * 6)
        else:
            for i in range(1, 7):
                row.append(int(pos.get(i, 0)))

        self._writer.writerow(row)
        self.state.rows += 1
        if self.state.rows % 10 == 0:
            self._fh.flush()

    def stop(self) -> None:
        try:
            if self._fh:
                self._fh.flush()
                self._fh.close()
        finally:
            self._fh = None
            self._writer = None
            self.state = None
