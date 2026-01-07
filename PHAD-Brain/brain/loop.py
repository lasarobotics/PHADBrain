# brain/loop.py
"""
Main brain loop.

Pipeline:
1. Sense   -> read NT4 (robot + vision)
2. Think   -> decide intent (planner / ML later)
3. Act     -> publish intent back to RoboRIO
"""

import time
from typing import Dict, Any

from brain.comms import NT4Client


class BrainLoop:
    def __init__(self, nt4: NT4Client):
        self.nt4 = nt4
        self._seq = 0
        self._running = True

    # -----------------------------
    # Public runner
    # -----------------------------
    def run(self) -> None:
        print("[PHAD] Brain loop started")

        dt = 1.0 / 50.0  # brain tick (independent of NT poll rate)

        while self._running:
            t0 = time.time()

            # 1. SENSE
            obs = self._sense()

            # 2. THINK
            intent = self._think(obs)

            # 3. ACT
            self._act(intent)

            # Rate control
            elapsed = time.time() - t0
            sleep_time = max(0.0, dt - elapsed)
            time.sleep(sleep_time)

    # -----------------------------
    # Sense
    # -----------------------------
    def _sense(self) -> Dict[str, Any]:
        """
        Pull latest cached data from NT4.
        """
        rio = self.nt4.get_rio_data()
        at = self.nt4.get_apriltags_PHAD()
        nd = self.nt4.get_neural_PHAD()

        return {
            "rio": rio,
            "apriltags": at,
            "neural": nd,
        }

    # -----------------------------
    # Think
    # -----------------------------
    def _think(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide what the robot should do next.
        Replace this with:
        - state fusion
        - planner
        - ML policy
        """

        self._seq += 1

        # Example: do nothing unless we see an AprilTag
        at = obs["apriltags"]

        if at and at.valid:
            intent = {
                "type": "TRACK_TAG",
                "tid": at.tid,
                "tx_deg": at.tx_deg,
                "ty_deg": at.ty_deg,
            }
        else:
            intent = {
                "type": "IDLE"
            }

        return {
            "seq": self._seq,
            "intent": intent,
        }

    # -----------------------------
    # Act
    # -----------------------------
    def _act(self, decision: Dict[str, Any]) -> None:
        """
        Publish high-level intent to RoboRIO.
        """
        self.nt4.publish_intent(decision)
