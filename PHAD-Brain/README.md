# PHAD-Brain — Quick Run Guide

This is the **minimal guide** to get PHAD-Brain running and training models.

---

## Requirements
- Python **3.9 – 3.11**
- RoboRIO on the same network (for runtime)
- Limelight (optional for training, required for vision)

---

## Install
From the project root:
```bash
pip install -r requirements.txt
Run PHAD-Brain
Starts the brain loop and connects to RoboRIO via NetworkTables.

bash
Copy code
python -m brain.app
What it does:

Reads robot + Limelight data

Decides high-level intent

Publishes intent back to RoboRIO

Train Limelight Neural Model
From LLtrainingModel/:

bash
Copy code
python train.py
You will be prompted to select:

dataSet1 or dataSet2

Outputs:

limelight_model.onnx

limelight_model.tflite

Upload the .tflite model to Limelight.

Dataset Format
Copy code
dataSetX/
├── class1/
├── class2/
Notes
PHAD-Brain does not control motors

RoboRIO owns final actuation

Limelight models must stay small for FPS

That’s it. Run → Train → Deploy.