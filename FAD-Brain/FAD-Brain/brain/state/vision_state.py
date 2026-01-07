from networktables import NetworkTables
import time
import threading

TEAM_NUMBER = 418


class VisionStatePHAD:
    """
    Stores latest valid Limelight vision data locally for PHAD-Brain.
    """

    def __init__(self):
        self._lock = threading.Lock()

        # -------------------------
        # APRILTAG (AT) DATA
        # -------------------------
        self.botposeAT_PHAD = None
        self.tidAT_PHAD = None
        self.validAT_PHAD = False

        # -------------------------
        # NEURAL DETECTION (ND) DATA
        # -------------------------
        self.txND_PHAD = None
        self.tyND_PHAD = None
        self.taND_PHAD = None
        self.rawdetectionsND_PHAD = None
        self.validND_PHAD = False

    # -------------------------
    # UPDATE METHODS (internal)
    # -------------------------
    def _update_apriltag(self, ll_left):
        tv = ll_left.getNumber("tv", 0)

        with self._lock:
            if tv == 1:
                self.botposeAT_PHAD = ll_left.getNumberArray(
                    "botpose_wpiblue", [0] * 6
                )
                self.tidAT_PHAD = ll_left.getNumber("tid", -1)
                self.validAT_PHAD = True
            else:
                self.validAT_PHAD = False

    def _update_neural(self, ll_right):
        tv = ll_right.getNumber("tv", 0)

        with self._lock:
            if tv == 1:
                self.txND_PHAD = ll_right.getNumber("tx", 0.0)
                self.tyND_PHAD = ll_right.getNumber("ty", 0.0)
                self.taND_PHAD = ll_right.getNumber("ta", 0.0)
                self.rawdetectionsND_PHAD = ll_right.getNumberArray(
                    "rawdetections", []
                )
                self.validND_PHAD = True
            else:
                self.validND_PHAD = False

    # -------------------------
    # PUBLIC GETTERS (SAFE)
    # -------------------------
    def get_apriltag(self):
        with self._lock:
            return {
                "valid": self.validAT_PHAD,
                "botpose": self.botposeAT_PHAD,
                "tag_id": self.tidAT_PHAD,
            }

    def get_neural(self):
        with self._lock:
            return {
                "valid": self.validND_PHAD,
                "tx": self.txND_PHAD,
                "ty": self.tyND_PHAD,
                "ta": self.taND_PHAD,
                "detections": self.rawdetectionsND_PHAD,
            }
