# laptop/net_sender.py
from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Optional


@dataclass
class SenderStats:
    connected: bool = False
    sent: int = 0


class TeleopSender:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = int(port)
        self.sock: Optional[socket.socket] = None
        self.stats = SenderStats()

    def connect(self, timeout_s: float = 3.0) -> None:
        self.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout_s)
        s.connect((self.host, self.port))
        s.settimeout(None)
        self.sock = s
        self.stats.connected = True

    def send_json_line(self, obj: dict) -> None:
        if not self.sock:
            raise RuntimeError("Not connected")
        line = json.dumps(obj, separators=(",", ":")) + "\n"
        self.sock.sendall(line.encode("utf-8"))
        self.stats.sent += 1

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None
        self.stats.connected = False
