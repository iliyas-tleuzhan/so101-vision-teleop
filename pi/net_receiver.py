# pi/net_receiver.py
from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from common.message_schema import validate_cmd, to_command, TeleopCommand
from common.timeutil import now_s


@dataclass
class NetStats:
    last_seq: int = -1
    last_recv_mono_s: float = 0.0
    rx_count: int = 0
    seq_gaps: int = 0


class NDJSONTCPServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = int(port)
        self.stats = NetStats()

    def listen_accept(self) -> socket.socket:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self.host, self.port))
        srv.listen(1)
        print(f"[pi] Listening on {self.host}:{self.port} ...")
        conn, addr = srv.accept()
        print(f"[pi] Client connected from {addr}")
        srv.close()
        return conn

    def recv_loop(self, conn: socket.socket):
        buf = ""
        conn.settimeout(0.5)
        while True:
            try:
                data = conn.recv(4096)
                if not data:
                    raise ConnectionError("client disconnected")
                buf += data.decode("utf-8", errors="replace")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    yield line
            except socket.timeout:
                continue
