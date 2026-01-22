# pi/server.py
from __future__ import annotations

import json
import traceback

from common.config import load_calibration, load_yaml
from common.message_schema import validate_cmd, to_command
from common.timeutil import now_s, sleep_s
from pi.dxl_driver import DxlConfig, DynamixelBus
from pi.logger import CSVLogger
from pi.net_receiver import NDJSONTCPServer
from pi.safety import SafetyLayer


def main() -> int:
    net_cfg = load_yaml("config/network.yaml")
    dxl_cfg_y = load_yaml("config/dynamixel.yaml")
    calib = load_calibration("config/robot_calibration.json")

    tcp = net_cfg["tcp"]
    host = "0.0.0.0"
    port = int(tcp["pi_port"])
    stale_timeout_s = float(tcp.get("stale_timeout_s", 0.35))
    hard_stop_timeout_s = float(tcp.get("hard_stop_timeout_s", 1.0))

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

    ids = [1, 2, 3, 4, 5, 6]
    bus = DynamixelBus(dxl_cfg, ids)
    safety = SafetyLayer(calib, stale_timeout_s=stale_timeout_s, hard_stop_timeout_s=hard_stop_timeout_s)

    logger = CSVLogger("logs")
    log_path = logger.start()
    print(f"[pi] Logging to {log_path}")

    # Default: torque on at start (safer to explicitly control)
    try:
        bus.open()
        bus.torque_all(True)
        print("[pi] Dynamixel bus opened, torque ON")
    except Exception as e:
        print("[pi] ERROR opening Dynamixel:", e)
        return 1

    server = NDJSONTCPServer(host, port)
    conn = server.listen_accept()

    last_targets = {i: int((calib[i].range_min + calib[i].range_max) / 2) for i in ids}

    enable_present = bool(dxl_cfg_y.get("behavior", {}).get("enable_present_read", False))
    present_hz = float(dxl_cfg_y.get("behavior", {}).get("present_read_hz", 10))
    present_period = 1.0 / max(1.0, present_hz)
    last_present_t = now_s()
    last_present = None

    try:
        for line in server.recv_loop(conn):
            try:
                msg = json.loads(line)
                ok, reason = validate_cmd(msg)
                if not ok:
                    print(f"[pi] DROP invalid msg: {reason}")
                    continue

                cmd = to_command(msg)
                home_req = bool(cmd.features.get("home", 0.0) >= 0.5)

                # Confidence gate: treat >= min_conf as OK (same as laptop default)
                # Pi is final authority though — if you want stricter safety, raise this.
                confidence_ok = cmd.confidence >= 0.60

                decision = safety.apply(
                    seq=cmd.seq,
                    estop=cmd.estop,
                    torque=cmd.torque,
                    confidence_ok=confidence_ok,
                    joints=cmd.joints,
                    home_req=home_req,
                )

                stale = safety.stale_policy()
                mode = decision["mode"]

                # Apply stale policy
                if stale == "HARD_STOP":
                    # optional: torque off after prolonged stale
                    try:
                        bus.torque_all(False)
                    except Exception:
                        pass
                    mode = "HARD_STOP"
                elif stale == "SOFT_HOLD" and mode == "LOW_CONF":
                    mode = "SOFT_HOLD"

                # Apply torque state (unless estop/hard stop overrides)
                torque_should_be = bool(decision["torque"]) and stale != "HARD_STOP"
                try:
                    bus.torque_all(torque_should_be)
                except Exception as e:
                    print("[pi] WARN torque_all failed:", e)

                # Apply motion if we have joints this tick
                if decision["joints"] is not None and stale != "HARD_STOP":
                    last_targets = decision["joints"]
                    bus.sync_write_positions(last_targets)

                # Optional present read
                if enable_present and (now_s() - last_present_t) >= present_period:
                    try:
                        last_present = bus.sync_read_positions()
                    except Exception as e:
                        print("[pi] WARN present read failed:", e)
                        last_present = None
                    last_present_t = now_s()

                logger.write(
                    seq=cmd.seq,
                    confidence=cmd.confidence,
                    mode=mode,
                    estop=cmd.estop,
                    torque=torque_should_be,
                    features=cmd.features,
                    cmd=last_targets,
                    pos=last_present,
                )

            except Exception as e:
                print("[pi] ERROR processing line:", e)
                traceback.print_exc()

    except Exception as e:
        print("[pi] Connection ended:", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass
        logger.stop()
        try:
            bus.torque_all(False)
        except Exception:
            pass
        bus.close()
        print("[pi] Shutdown complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
