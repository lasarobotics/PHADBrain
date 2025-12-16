# PHAD-Brain 🧠🤖  
**Perception & High-level Autonomy Driver for FRC Robots**

PHAD-Brain is a **competition-grade, modular autonomy system** designed for FRC robots.  
It runs off-robot (laptop / coprocessor), communicates with the RoboRIO via **NetworkTables 4**, ingests **Limelight vision + robot state**, and outputs **high-level intent** (not motor commands).

This repo also contains **Limelight neural-detector training pipelines** (TensorFlow Lite + PyTorch), built to be fast, minimal, and match real FRC match constraints.

---

## 🧩 Project Goals
- Clean separation of **perception**, **state**, **planning**, and **actuation**
- Limelight-friendly neural models (small, fast, reliable)
- NT4-first communication (FRC-native)
- Deterministic, debuggable autonomy loops
- Worlds-ready architecture (no bloat, no magic)

---

## 📁 Repository Structure

PHAD-Brain/
├── brain/
│ ├── comms/ # NT4 + ZMQ communication layer
│ │ ├── protocol.py # Packet + vision data definitions
│ │ ├── nt4_client.py # RoboRIO & Limelight interface
│ │ └── zmq_client.py # Optional low-latency transport
│ ├── intent/ # (future) planners / decision logic
│ ├── model/ # (future) learned policies
│ ├── state/ # (future) sensor fusion / world model
│ ├── utils/
│ ├── app.py # Brain entry point
│ └── loop.py # Sense → Think → Act loop
│
├── LLtrainingModel/ # Limelight neural model training
│ ├── train.py # Unified training script (TFLite + ONNX)
│ ├── data/
│ │ ├── dataSet1/ # Dataset option 1
│ │ └── dataSet2/ # Dataset option 2
│ └── init.py
│
├── configs/ # Configs (future)
├── scripts/ # Utilities (future)
├── tests/ # Tests (future)
├── requirements.txt # Full dependency list
├── README.md
└── LICENSE

yaml
Copy code

---

## 🔁 Runtime Architecture

### 1️⃣ Sense
- Reads robot pose & velocity from RoboRIO (`FAD/*`)
- Reads AprilTag data from Limelight
- Reads Neural Detector output from Limelight
- All data cached locally in `NT4Client`

### 2️⃣ Think
- Combines robot + vision state
- Decides **intent** (ex: TRACK_TAG, IDLE, GOTO)
- No motor control here by design

### 3️⃣ Act
- Publishes intent back to RoboRIO (`PHAD/intent_json`)
- RoboRIO owns final control

---

## 📡 Communication
- **NetworkTables 4 (NT4)** – primary transport
- **ZMQ** – optional for future low-latency pipelines
- JSON-based intent messages
- Sequence + timestamped packets

---

## 🧠 Vision & Neural Detection
Supported vision inputs:
- Limelight AprilTags
- Limelight Neural Detector (classification)

Design rules:
- Only valid targets are propagated
- Vision is advisory, not authoritative
- Multiple Limelights supported (left/right roles)

---

## 🏋️ Limelight Neural Model Training

### Training Script
LLtrainingModel/train.py

markdown
Copy code

Features:
- Prompts user to select dataset:
  - `dataSet1`
  - `dataSet2`
- Trains **lightweight CNN**
- Exports:
  - `limelight_model.onnx`
  - `limelight_model.tflite`
- Dataset format matches Limelight native expectations

### Dataset Layout
dataSetX/
├── classA/
│ ├── img1.jpg
│ └── img2.jpg
├── classB/
│ ├── img1.jpg
│ └── img2.jpg

yaml
Copy code

---

## ⚙️ Installation

### Python Version
**Python 3.9 – 3.11 recommended**

### Install Dependencies
```bash
pip install -r requirements.txt
⚠️ On Windows, use tensorflow-cpu if CUDA causes issues.

▶️ Running PHAD-Brain
bash
Copy code
python -m brain.app
What happens:

Connects to RoboRIO via NT4

Starts main brain loop

Continuously publishes intent decisions

🧪 Current Status
✔ NT4 communication
✔ Limelight AprilTag ingestion
✔ Limelight Neural ingestion
✔ Deterministic brain loop
✔ Training pipeline (ONNX + TFLite)

🔜 Planned:

Sensor fusion (state/)

Field-relative planning

Confidence weighting

Multi-target arbitration

Match replay + logging

🏆 Design Philosophy
RoboRIO controls motors

Brain controls intent

Vision assists, never overrides

Simple beats clever in competition

This repo is built for real matches, not demos.

📜 License
MIT License — use, modify, compete.

👤 Author
PHAD-Brain
FRC-focused autonomy + perception stack

