# SO-101 Vision Teleoperation

Vision-based hand teleoperation for the LeRobot SO-101 robotic arm.

## Architecture
Laptop:
Webcam → MediaPipe → Hand Features → Joint Mapping → TCP Stream

Raspberry Pi:
TCP Receiver → Safety Layer → Dynamixel Driver → Servos

## Requirements
- Laptop: Python 3.10+, webcam
- Raspberry Pi 5
- SO-101 arm (IDs 1–6)

## Run
Laptop:
```bash
pip install -r laptop/requirements.txt
python laptop/app.py
