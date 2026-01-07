"""
PHAD-Brain comms package.

Supports:
- NT4 (NetworkTables 4) client for RoboRIO <-> Brain communication
- ZeroMQ (optional) low-latency message transport (Brain <-> RoboRIO bridge if you want)
"""

from .protocol import (
    RobotToBrainPacket,
    BrainToRobotPacket,
    VisionAprilTagsPHAD,
    VisionNeuralDetectionsPHAD,
    PHADNames,
    encode_packet,
    decode_packet,
)
from .nt4_client import NT4Client
from .zmq_client import ZMQClient

__all__ = [
    "RobotToBrainPacket",
    "BrainToRobotPacket",
    "VisionAprilTagsPHAD",
    "VisionNeuralDetectionsPHAD",
    "PHADNames",
    "encode_packet",
    "decode_packet",
    "NT4Client",
    "ZMQClient",
]
