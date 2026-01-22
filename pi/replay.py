# pi/replay.py
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from common.config import load_calibration, load_yaml
from common.timeutil import sleep_s
from pi.dxl_driver import DxlConfig, DynamixelBus


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=str, help="Path to a log CSV produced by pi/logger.py")
    ap.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier (1.0 = real-time)")
    args = ap.parse_args()

    net_cfg = load_yaml("config/network.yaml")
    dxl_cfg_y = load_yaml("config/dynamixel.yaml")
    calib = load_calibration("config/robot_calibration.json")

    ids = [1, 2, 3, 4, 5, 6]

    dxy = dxl_cfg_y["dynamixel"]
    cty = dxl_cfg_y["control_table"]
    dxl_cfg = DxlConfig(
        device=str(dxy["device"]),
        baudrate=int(dxy["baudrate"]),
        protocol_version=float(dxy["protocol_version"]),
        addr_torque_enable=int(cty["addr_torque_enable"]),
        addr_goal_position=int(cty["addr_goal_position"]),
        addr_present_position=int(cty["addr_present_position"]),
        len_goal_position=int(cty["len_goal_position"]),
        len_present_position=int(cty["len_present_position"]),
    )

    path = Path(args.csv_path)
    if not path.exists():
        print("CSV not found:", path)
        return 1

    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append(r)

    if len(rows) < 2:
        print("Not enough rows to replay.")
        return 1

    bus = DynamixelBus(dxl_cfg, ids)
    bus.open()
    bus.torque_all(True)

    t0 = float(rows[0]["wall_s"])
    for i in range(1, len(rows)):
        r_prev = rows[i - 1]
        r = rows[i]
        t_prev = float(r_prev["wall_s"])
        t = float(r["wall_s"])
        dt = max(0.0, (t - t_prev) / max(0.1, args.speed))

        targets = {j: int(r[f"cmd_j{j}"]) for j in ids}
        # Clamp to calibration hard limits (extra safety)
        for j in ids:
            lo, hi = calib[j].range_min, calib[j].range_max
            targets[j] = max(lo, min(hi, targets[j]))

        sleep_s(dt)
        bus.sync_write_positions(targets)

    bus.torque_all(False)
    bus.close()
    print("Replay complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
