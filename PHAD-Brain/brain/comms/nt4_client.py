from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import time

# NT4 python binding (WPILib)
# pip: ntcore
from ntcore import NetworkTableInstance

from .protocol import (
    VisionAprilTagsPHAD,
    VisionNeuralDetectionsPHAD,
    PHADNames,
    now_s,
)


@dataclass
class NT4Config:
    """
    server:
      - roborio-418-frc.local  (mDNS)
      - 10.4.18.2              (static)
    """
    server: str
    client_name: str = "PHAD-Brain"
    rio_table: str = "FAD"                # RoboRIO publishes pose/velocity here
    out_table: str = "PHAD"               # Brain publishes decisions here

    limelight_left: str = "limelight-left"
    limelight_right: str = "limelight-right"

    # If you run separate pipelines per limelight:
    # left_for_apriltags=True means left provides AT, right provides ND (or vice versa)
    left_for_apriltags: bool = True

    # read rate control
    poll_hz: float = 50.0


class NT4Client:
    """
    Connects to NT4 server (usually RoboRIO) and reads:
      - RoboRIO data table (pose/velocity/etc)
      - Limelight tables (AprilTag + Neural detection)
    Stores them locally for other files to call.
    """

    def __init__(self, cfg: NT4Config):
        self.cfg = cfg

        self._inst = NetworkTableInstance.getDefault()
        self._inst.setServer(cfg.server)
        self._inst.startClient4(cfg.client_name)

        # Tables
        self._rio = self._inst.getTable(cfg.rio_table)
        self._out = self._inst.getTable(cfg.out_table)
        self._ll_left = self._inst.getTable(cfg.limelight_left)
        self._ll_right = self._inst.getTable(cfg.limelight_right)

        # Local cache (what other modules will “call”)
        self._last_rio: Dict[str, Any] = {}
        self._last_at: Optional[VisionAprilTagsPHAD] = None
        self._last_nd: Optional[VisionNeuralDetectionsPHAD] = None

        self._seq = 0

    # -------------------------
    # Connection / status
    # -------------------------
    def is_connected(self) -> bool:
        return self._inst.isConnected()

    def wait_for_connection(self, timeout_s: float = 5.0) -> bool:
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            if self.is_connected():
                return True
            time.sleep(0.05)
        return self.is_connected()

    # -------------------------
    # Public getters (local store)
    # -------------------------
    def get_rio_data(self) -> Dict[str, Any]:
        """Latest RoboRIO data snapshot (pose/velocity/etc)."""
        return dict(self._last_rio)

    def get_apriltags_PHAD(self) -> Optional[VisionAprilTagsPHAD]:
        """Latest AprilTag snapshot (PHAD naming), or None if never valid."""
        return self._last_at

    def get_neural_PHAD(self) -> Optional[VisionNeuralDetectionsPHAD]:
        """Latest Neural snapshot (PHAD naming), or None if never valid."""
        return self._last_nd

    # -------------------------
    # Write outputs (brain -> rio)
    # -------------------------
    def publish_intent(self, intent: Dict[str, Any]) -> None:
        """
        Publishes a JSON string under PHAD/intent_json and a seq/timestamp.
        RoboRIO can parse it however you want.
        """
        self._seq += 1
        self._out.getEntry("seq").setInteger(self._seq)
        self._out.getEntry("timestamp_s").setDouble(now_s())
        self._out.getEntry("intent_json").setString(_safe_json(intent))

    # -------------------------
    # Main poller
    # -------------------------
    def poll_once(self) -> None:
        """
        Pull newest values from:
          - RoboRIO table (pose/velocity/vision/* if you publish it)
          - Limelights (AT + ND)
        and cache locally.
        """
        self._poll_rio()
        self._poll_limelights()

    def loop_forever(self) -> None:
        dt = 1.0 / max(self.cfg.poll_hz, 1e-6)
        while True:
            self.poll_once()
            time.sleep(dt)

    # -------------------------
    # Internal polling helpers
    # -------------------------
    def _poll_rio(self) -> None:
        # These keys match the code you showed earlier (pose, velocity, vision/left, vision/right)
        pose = self._rio.getEntry("pose").getDoubleArray([0.0, 0.0, 0.0])
        vel = self._rio.getEntry("velocity").getDoubleArray([0.0, 0.0, 0.0])

        # Optional vision confidence arrays published by RoboRIO (if you do it)
        vleft = self._rio.getEntry("vision/left").getDoubleArray([0.0])
        vright = self._rio.getEntry("vision/right").getDoubleArray([0.0])

        self._last_rio = {
            "pose": pose,
            "velocity": vel,
            "vision_left_conf": vleft,
            "vision_right_conf": vright,
            "timestamp_s": now_s(),
        }

    def _poll_limelights(self) -> None:
        # Decide which limelight is responsible for AT vs ND
        at_table = self._ll_left if self.cfg.left_for_apriltags else self._ll_right
        nd_table = self._ll_right if self.cfg.left_for_apriltags else self._ll_left

        self._last_at = self._read_apriltags(at_table)
        self._last_nd = self._read_neural(nd_table)

    def _read_apriltags(self, ll) -> Optional[VisionAprilTagsPHAD]:
        tv = ll.getEntry("tv").getDouble(0.0)
        tid = int(ll.getEntry("tid").getDouble(-1.0))

        # Only “valid” if tv==1 and tid present
        valid = (tv == 1.0) and (tid != -1)

        if not valid:
            return None

        tx = ll.getEntry("tx").getDouble(0.0)
        ty = ll.getEntry("ty").getDouble(0.0)
        ta = ll.getEntry("ta").getDouble(0.0)

        botpose_wpiblue = ll.getEntry("botpose_wpiblue").getDoubleArray([])
        botpose_wpired = ll.getEntry("botpose_wpired").getDoubleArray([])
        targetpose_robotspace = ll.getEntry("targetpose_robotspace").getDoubleArray([])
        rawfiducials = ll.getEntry("rawfiducials").getDoubleArray([])

        return VisionAprilTagsPHAD(
            valid=True,
            tid=tid,
            tx_deg=tx,
            ty_deg=ty,
            ta=ta,
            botpose_wpiblue=list(botpose_wpiblue),
            botpose_wpired=list(botpose_wpired),
            targetpose_robotspace=list(targetpose_robotspace),
            rawfiducials=list(rawfiducials),
            timestamp_s=now_s(),
        )

    def _read_neural(self, ll) -> Optional[VisionNeuralDetectionsPHAD]:
        tv = ll.getEntry("tv").getDouble(0.0)
        valid = (tv == 1.0)

        if not valid:
            return None

        tx = ll.getEntry("tx").getDouble(0.0)
        ty = ll.getEntry("ty").getDouble(0.0)
        ta = ll.getEntry("ta").getDouble(0.0)

        tclass = ll.getEntry("tclass").getString("")
        tdclass = ll.getEntry("tdclass").getString("")
        rawdetections = ll.getEntry("rawdetections").getDoubleArray([])

        return VisionNeuralDetectionsPHAD(
            valid=True,
            tx_deg=tx,
            ty_deg=ty,
            ta=ta,
            tclass=tclass,
            tdclass=tdclass,
            rawdetections=list(rawdetections),
            timestamp_s=now_s(),
        )


def _safe_json(obj: Any) -> str:
    import json
    try:
        return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    except Exception:
        return "{}"
