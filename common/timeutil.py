# common/timeutil.py
from __future__ import annotations

import time


def now_s() -> float:
    # monotonic for timing
    return time.monotonic()


def wall_time_s() -> float:
    # wall clock for logs
    return time.time()


def sleep_s(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)
