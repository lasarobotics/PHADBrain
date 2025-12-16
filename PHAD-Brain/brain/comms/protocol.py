from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple, Literal
import json
import time


# -----------------------------
# Naming: keep everything PHAD-safe
# -----------------------------
class PHADNames:
    """
    Central place for the exact key names you want stored in Python.
    Suffixes:
      ND = Neural Detection
      AT = April Tags
      PHAD = your disambiguation tag
    """

    # AprilTag basic targeting
    tv_AT_PHAD = "tvATphad"
    tx_AT_PHAD = "txATphad"
    ty_AT_PHAD = "tyATphad"
    ta_AT_PHAD = "taATphad"
    tid_AT_PHAD = "tidATphad"
    botpose_wpiblue_AT_PHAD = "botposeWpiblueATphad"
    botpose_wpired_AT_PHAD = "botposeWpiredATphad"
    targetpose_robotspace_AT_PHAD = "targetposeRobotspaceATphad"
    rawfiducials_AT_PHAD = "rawfiducialsATphad"

    # Neural detection basics
    tv_ND_PHAD = "tvNDphad"
    tx_ND_PHAD = "txNDphad"
    ty_ND_PHAD = "tyNDphad"
    ta_ND_PHAD = "taNDphad"
    tclass_ND_PHAD = "tclassNDphad"
    tdclass_ND_PHAD = "tdclassNDphad"
    rawdetections_ND_PHAD = "rawdetectionsNDphad"

    # Timestamping / sequence
    timestamp_s = "timestamp_s"
    seq = "seq"


@dataclass
class VisionAprilTagsPHAD:
    """AprilTag-related values from a Limelight table, with validity checks applied."""
    valid: bool
    tid: int
    tx_deg: float
    ty_deg: float
    ta: float

    # arrays (Limelight returns meters/degrees arrays; keep raw)
    botpose_wpiblue: List[float]
    botpose_wpired: List[float]
    targetpose_robotspace: List[float]
    rawfiducials: List[float]

    # metadata
    timestamp_s: float


@dataclass
class VisionNeuralDetectionsPHAD:
    """Neural detector values (primary target + raw detections)."""
    valid: bool
    tx_deg: float
    ty_deg: float
    ta: float
    tclass: str
    tdclass: str
    rawdetections: List[float]
    timestamp_s: float


@dataclass
class RobotToBrainPacket:
    """
    What RoboRIO publishes for the brain.
    Keep it minimal: pose/velocity and any robot-state you want.
    """
    seq: int
    timestamp_s: float

    # Pose (field or odom) and velocity
    pose: Tuple[float, float, float]          # x, y, heading (units you choose)
    velocity: Tuple[float, float, float]      # vx, vy, omega (units you choose)

    # Optional: subsystem states (free-form)
    subsystem: Dict[str, Any]


@dataclass
class BrainToRobotPacket:
    """
    What the brain sends back: high-level decisions / intents (no motor control here).
    """
    seq: int
    timestamp_s: float

    # Example intent fields (edit later)
    mode: Literal["DISABLED", "TELEOP", "AUTO", "TEST"]
    intent: Dict[str, Any]   # e.g. {"type": "GOTO", "x": 2.1, "y": 5.4, "heading": 90}


# -----------------------------
# Serialization helpers
# -----------------------------
def now_s() -> float:
    return time.time()


def encode_packet(packet: Any) -> bytes:
    """Encode dataclass -> JSON bytes."""
    if hasattr(packet, "__dataclass_fields__"):
        payload = asdict(packet)
    else:
        payload = packet
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_packet(data: bytes) -> Dict[str, Any]:
    """Decode JSON bytes -> dict."""
    return json.loads(data.decode("utf-8"))
