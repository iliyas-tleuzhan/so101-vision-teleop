# laptop/app.py
from __future__ import annotations

import sys
import time

import cv2

from common.config import load_calibration, load_yaml
from common.timeutil import wall_time_s, sleep_s
from laptop.features import FeatureExtractor
from laptop.hand_tracking import MediaPipeHandTracker
from laptop.keyboard import KeyboardController
from laptop.mapping import HandToJointMapper
from laptop.net_sender import TeleopSender


def main() -> int:
    mapping_cfg = load_yaml("config/mapping.yaml")
    net_cfg = load_yaml("config/network.yaml")
    calib = load_calibration("config/robot_calibration.json")

    tcp = net_cfg["tcp"]
    host = tcp["pi_host"]
    port = int(tcp["pi_port"])
    send_hz = float(tcp.get("send_hz", 30))
    period = 1.0 / max(1.0, send_hz)

    fx_cfg = mapping_cfg["features"]
    extractor = FeatureExtractor(
        ema_alpha=fx_cfg["ema_alpha"],
        dz_wrist_xy=fx_cfg["deadzone_wrist_xy"],
        dz_roll=fx_cfg["deadzone_roll"],
        dz_pinch=fx_cfg["deadzone_pinch"],
    )
    mapper = HandToJointMapper(mapping_cfg, calib)

    gate_cfg = mapping_cfg["confidence_gate"]
    min_conf = float(gate_cfg["min_confidence"])
    hold_last = bool(gate_cfg["hold_last_on_low_conf"])

    tracker = MediaPipeHandTracker(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    sender = TeleopSender(host, port)
    print(f"[laptop] Connecting to Pi {host}:{port} ...")
    sender.connect()
    print("[laptop] Connected.")

    kb = KeyboardController()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open webcam.")
        return 1

    seq = 0
    last_joints = {i: int((calib[i].range_min + calib[i].range_max) / 2) for i in range(1, 7)}
    last_send = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            print("WARN: camera read failed")
            continue

        res = tracker.process(frame)
        kb.poll()

        if kb.quit:
            break

        # Build command
        cmd_joints = last_joints
        confidence = 0.0
        features = {
            "wrist_x": extractor.state.wrist_x,
            "wrist_y": extractor.state.wrist_y,
            "index_mcp_y": extractor.state.index_mcp_y,
            "pinch": extractor.state.pinch,
            "roll": extractor.state.roll,
            "home": 1.0 if kb.consume_home_request() else 0.0,
        }

        if res is not None:
            confidence = float(res.score)
            features = extractor.extract(res.landmarks) | {
                "home": 1.0 if kb.consume_home_request() else 0.0
            }
            if confidence >= min_conf:
                cmd_joints = mapper.map(features)
                last_joints = cmd_joints
            else:
                # Confidence gate behavior
                if not hold_last:
                    cmd_joints = last_joints  # keep but you could also freeze-sending if desired

            frame_show = res.image_bgr
        else:
            frame_show = frame.copy()

        # HUD
        hud = f"seq={seq} conf={confidence:.2f} EStop={kb.estop} Torque={kb.torque}"
        cv2.putText(frame_show, hud, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame_show, "Keys: e=ESTOP  t=TORQUE  h=HOME  q=QUIT",
                    (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        # Rate limit sending
        now = time.perf_counter()
        if now - last_send >= period:
            msg = {
                "type": "cmd",
                "seq": seq,
                "ts": wall_time_s(),
                "confidence": confidence if res is not None else 0.0,
                "estop": kb.estop,
                "torque": kb.torque,
                "joints": {str(k): int(v) for k, v in cmd_joints.items()},
                "features": {k: float(v) for k, v in features.items()},
            }
            try:
                sender.send_json_line(msg)
            except Exception as e:
                cv2.putText(frame_show, f"NET ERROR: {e}", (10, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            seq += 1
            last_send = now

        cv2.imshow("SO101 Vision Teleop (Laptop)", frame_show)

    cap.release()
    sender.close()
    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
