from networktables import NetworkTables
import time

TEAM_NUMBER = 418


# NEED TO DO:
# need to get tx, ty, etc for NEURAL DETECTION and for april tags, and like assign what LL is doing what role so we dont have to swithc pipelines
def init_nt():
    # Connect directly to team 418 RoboRIO - change team number if trying to connect to 436
    NetworkTables.initialize(server=f"roborio-{TEAM_NUMBER}-frc.local")

    print("Trying to connect to NetworkTables connection")
    while not NetworkTables.isConnected():
        time.sleep(0.1)

    print("Successful connection to NetworkTables connection")

def main():
    init_nt()

    table = NetworkTables.getTable("FAD")

    while True:
        pose = table.getNumberArray("pose", [0.0, 0.0, 0.0])
        velocity = table.getNumberArray("velocity", [0.0, 0.0, 0.0])
        vision_left = table.getNumberArray("vision/left", [0.0])
        vision_right = table.getNumberArray("vision/right", [0.0])

        print(f"Pose: {pose}")
        print(f"Velocity: {velocity}")
        print(f"Vision LL L: {vision_left} | Vision LL R: {vision_right}")
        print("------")

        time.sleep(0.05)  # 20 Hz SPEED

if __name__ == "__main__":
    main()
