# pi/dxl_driver.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from dynamixel_sdk import (
    PortHandler,
    PacketHandler,
    GroupSyncWrite,
    GroupSyncRead,
)


def _int_to_le_bytes(val: int, length: int) -> bytes:
    return int(val).to_bytes(length, byteorder="little", signed=False)


@dataclass
class DxlConfig:
    device: str
    baudrate: int
    protocol_version: float
    addr_torque_enable: int
    addr_goal_position: int
    addr_present_position: int
    len_goal_position: int
    len_present_position: int


class DynamixelBus:
    def __init__(self, cfg: DxlConfig, motor_ids: List[int]) -> None:
        self.cfg = cfg
        self.ids = list(motor_ids)

        self.port = PortHandler(cfg.device)
        self.packet = PacketHandler(cfg.protocol_version)

        self.sync_write = GroupSyncWrite(self.port, self.packet, cfg.addr_goal_position, cfg.len_goal_position)
        self.sync_read = GroupSyncRead(self.port, self.packet, cfg.addr_present_position, cfg.len_present_position)

        self.is_open = False

    def open(self) -> None:
        if not self.port.openPort():
            raise RuntimeError(f"Failed to open port {self.cfg.device}")
        if not self.port.setBaudRate(int(self.cfg.baudrate)):
            raise RuntimeError(f"Failed to set baudrate {self.cfg.baudrate}")
        self.is_open = True

        # Prepare sync read params
        for mid in self.ids:
            if not self.sync_read.addParam(mid):
                raise RuntimeError(f"Failed to addParam for sync_read id={mid}")

    def close(self) -> None:
        try:
            if self.is_open:
                self.port.closePort()
        finally:
            self.is_open = False

    def torque_enable(self, mid: int, enable: bool) -> None:
        val = 1 if enable else 0
        dxl_comm_result, dxl_error = self.packet.write1ByteTxRx(
            self.port, mid, self.cfg.addr_torque_enable, val
        )
        if dxl_comm_result != 0:
            raise RuntimeError(f"Torque write comm error id={mid}: {self.packet.getTxRxResult(dxl_comm_result)}")
        if dxl_error != 0:
            raise RuntimeError(f"Torque write dxl error id={mid}: {self.packet.getRxPacketError(dxl_error)}")

    def torque_all(self, enable: bool) -> None:
        for mid in self.ids:
            self.torque_enable(mid, enable)

    def sync_write_positions(self, targets: Dict[int, int]) -> None:
        self.sync_write.clearParam()
        for mid in self.ids:
            if mid not in targets:
                continue
            param = _int_to_le_bytes(targets[mid], self.cfg.len_goal_position)
            if not self.sync_write.addParam(mid, param):
                raise RuntimeError(f"Failed to addParam for sync_write id={mid}")

        dxl_comm_result = self.sync_write.txPacket()
        if dxl_comm_result != 0:
            raise RuntimeError(f"SyncWrite comm error: {self.packet.getTxRxResult(dxl_comm_result)}")

    def sync_read_positions(self) -> Dict[int, int]:
        dxl_comm_result = self.sync_read.txRxPacket()
        if dxl_comm_result != 0:
            raise RuntimeError(f"SyncRead comm error: {self.packet.getTxRxResult(dxl_comm_result)}")

        out: Dict[int, int] = {}
        for mid in self.ids:
            if self.sync_read.isAvailable(mid, self.cfg.addr_present_position, self.cfg.len_present_position):
                out[mid] = self.sync_read.getData(mid, self.cfg.addr_present_position, self.cfg.len_present_position)
        return out

    def ping(self, mid: int) -> bool:
        _, dxl_comm_result, dxl_error = self.packet.ping(self.port, mid)
        return (dxl_comm_result == 0 and dxl_error == 0)
