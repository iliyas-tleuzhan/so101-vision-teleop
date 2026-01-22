# scripts/pi_port_test.py
import serial

# Quick test that /dev/ttyUSB* is accessible (requires pyserial)
# pip install pyserial
PORT = "/dev/ttyUSB0"
BAUD = 1000000

with serial.Serial(PORT, BAUD, timeout=1) as s:
    print("Opened", PORT, "at", BAUD)
