# SO101 Vision-Assisted Teleoperation
## **Vision-assisted hand-tracking teleoperation for the LeRobot SO101 robotic arm**

### This project implements a **real-time, vision-assisted teleoperation system** for a 6-DOF LeRobot SO101 robotic arm using:
1) Laptop-side computer vision (MediaPipe Hands)
2) Network-based command streaming
3) Raspberry Pi 5 as a safety-critical robot controller
4) Dynamixel-style smart servos on a TTL serial bus

### This system is **not autonomous**.  
All robot motion is directly driven by a human operator’s hand movement and is continuously supervised by safety constraints on the Raspberry Pi.

### The project is designed as a **portfolio-quality robotics system** demonstrating computer vision, embedded control, networking, and safety-aware software architecture.

## Project goal
The primary goal of this project is to build a **robust, safe, and understandable teleoperation system** suitable for a robotics and computer engineering portfolio.

---
## Hardware topology
Laptop (Windows)
  - Webcam
  - Hand tracking + mapping
  - TCP command sender
    
        TCP (NDJSON)

### Raspberry Pi 5
  - Safety + validation
  - Logging + replay
  - Dynamixel SDK

        USB ↔ TTL adapter (/dev/ttyUSB*)

### TTL smart servo bus (IDs 1–6)
  - External power supply
### Key notes:
   - Laptop and Pi must be on the same network.
   - Servos require external power (USB is insufficient).
   - Servo power ground must be shared with the USB↔TTL adapter.

## Operator controls
Keyboard input is handled on the laptop while the application window is focused.

Controls:
- `e` — emergency stop (torque off)
- `t` — toggle torque enable
- `h` — move to safe home pose
- `q` — quit application

Emergency stop should always be tested before enabling motion.

## Setup

### Laptop (Windows)
1) Create venv and install dependencies:
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r laptop/requirements.txt
Set the Raspberry Pi IP in config/network.yaml
```
2) Run:
```bash
python laptop/app.py
```

### Raspberry Pi
1) Add user to serial group:
```bash
sudo usermod -aG dialout $USER
sudo reboot
```
2) Create venv and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r pi/requirements.txt
```
3) Configure config/dynamixel.yaml, then run:
```bash
python pi/server.py
```
