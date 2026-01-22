
# laptop/keyboard.py
from __future__ import annotations

import cv2


class KeyboardController:
    """
    Uses cv2.waitKey polling (works on Windows without extra deps).
    Controls:
      1) 'e' toggle E-STOP
      2) 't' toggle torque enable
      3) 'h' request safe home (sent as a flag via estop/torque + separate key in features)
      4) 'q' quit
    """

    def __init__(self) -> None:
        self.estop = False
        self.torque = True
        self.home_request = False
        self.quit = False

    def poll(self) -> None:
        key = cv2.waitKey(1) & 0xFF
        if key == ord("e"):
            self.estop = not self.estop
        elif key == ord("t"):
            self.torque = not self.torque
        elif key == ord("h"):
            self.home_request = True
        elif key == ord("q"):
            self.quit = True

    def consume_home_request(self) -> bool:
        if self.home_request:
            self.home_request = False
            return True
        return False
