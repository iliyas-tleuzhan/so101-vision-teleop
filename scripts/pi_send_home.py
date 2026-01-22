# scripts/pi_send_home.py
from common.config import load_calibration, load_yaml
from pi.dxl_driver import DxlConfig, DynamixelBus

def main():
    calib = load_calibration("config/robot_calibration.json")
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
    home = {i: int((calib[i].range_min + calib[i].range_max)/2) for i in ids}

    bus = DynamixelBus(cfg, ids)
    bus.open()
    bus.torque_all(True)
    bus.sync_write_positions(home)
    bus.close()
    print("Sent home pose")

if __name__ == "__main__":
    main()
