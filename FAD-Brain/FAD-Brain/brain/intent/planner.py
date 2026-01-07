from brain.state.vision_state import VisionStatePHAD

vision = VisionStatePHAD()

apriltag = vision.get_apriltag()
neural = vision.get_neural()

if apriltag["valid"]:
    pose = apriltag["botpose"]

if neural["valid"]:
    tx = neural["tx"]
