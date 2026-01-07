from networktables import NetworkTables
import time
from brain.state.vision_state import VisionStatePHAD

TEAM_NUMBER = 418


def init_nt():
    NetworkTables.initialize(server=f"roborio-{TEAM_NUMBER}-frc.local")
    while not NetworkTables.isConnected():
        time.sleep(0.1)
    print("PHAD NT connected")
    print("WORKING NT TABLE should be getting data")


def start_vision_listener(vision_state: VisionStatePHAD):
    init_nt()

    ll_left = NetworkTables.getTable("limelight-left")    # AprilTags
    ll_right = NetworkTables.getTable("limelight-right")  # Neural

    while True:
        vision_state._update_apriltag(ll_left)
        vision_state._update_neural(ll_right)
        time.sleep(0.02)  # 50 Hz
 