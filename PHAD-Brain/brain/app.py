# brain/app.py
"""
PHAD-Brain main entry point.

Responsibilities:
- Load configs
- Initialize comms (NT4, optional ZMQ later)
- Start the main brain loop
"""

from brain.comms import NT4Client
from brain.comms.nt4_client import NT4Config
from brain.loop import BrainLoop


def main() -> None:
    # -----------------------------
    # NT4 configuration
    # -----------------------------
    nt4_cfg = NT4Config(
        server="roborio-418-frc.local",  # change if needed
        client_name="PHAD-Brain",
        rio_table="FAD",
        out_table="PHAD",
        limelight_left="limelight-left",
        limelight_right="limelight-right",
        left_for_apriltags=True,
        poll_hz=50.0,
    )

    # -----------------------------
    # Initialize comms
    # -----------------------------
    nt4 = NT4Client(nt4_cfg)

    print("[PHAD] Waiting for NT4 connection...")
    if not nt4.wait_for_connection(timeout_s=5.0):
        print("[PHAD] ⚠️  Warning: NT4 not connected yet")
    else:
        print("[PHAD] ✅ NT4 connected")

    # -----------------------------
    # Start brain loop
    # -----------------------------
    brain = BrainLoop(nt4)
    brain.run()


if __name__ == "__main__":
    main()
