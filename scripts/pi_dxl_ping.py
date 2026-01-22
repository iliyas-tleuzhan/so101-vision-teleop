# scripts/pi_dxl_ping.py
from common.config import load_yaml
from pi.dxl_driver import DxlConfig, DynamixelBus

def main():
    dxl_cfg_y = load_yaml("config/dynamixel.yaml")
    dxy = dxl_cfg_y["dynamixel"]
    cty = dxl_cfg_y["control_table"]

    cfg = DxlConfig(
        device=str(dxy["device"]),
        baudrate=int(dxy["baudrate"]),
        protocol_version=float(dxy["protocol_version"]),
        addr_torque_enable=int(cty["addr_torque_enable"]),
        addr_goal_position=int(cty["addr_goal_position"]),
        addr_present_position=int(cty["addr_present_position"]),
        len_goal_position=int(cty["len_goal_position"]),
        len_present_position=int(cty["len_present_position"]),
    )

    ids = [1,2,3,4,5,6]
    bus = DynamixelBus(cfg, ids)
    bus.open()
    for mid in ids:
        ok = bus.ping(mid)
        print(f"PING id={mid}: {'OK' if ok else 'FAIL'}")
    bus.close()

if __name__ == "__main__":
    main()
