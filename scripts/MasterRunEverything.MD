How to run
- Open Command Prompt (Run as ADMIN).
- cd into the repo root.
- Run: `scripts\MasterRunEverything.bat`
- Pick an option from the menu:
  - 1: Run `vision_fusion.py`
  - 2: Run `limelight_pose.py`
  - 3: Full Run (current order: `vision_fusion.py` then `limelight_pose.py`; update this option if the sequence changes)
- Logs are written to `logs/<timestamp>/run.log` for each run and also echoed to separate command windows via PowerShell Tee with the purple-themed menu.
