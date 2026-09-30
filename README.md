# SafeSight AI / BlindSpot Project

> **Intelligent Multi-Modal Blind Spot Detection & Safety Zone Monitoring for Heavy Construction Equipment**

[![Unity 6](https://img.shields.io/badge/Unity-6000.0-blue.svg)](https://unity.com/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-red.svg)](https://ultralytics.com/)
[![ESP32](https://img.shields.io/badge/Hardware-ESP32-orange.svg)](https://www.espressif.com/)

---

## 📌 Overview

The **SafeSight AI / BlindSpot Project** is an end-to-end industrial safety solution designed to prevent blind-spot collisions and hazards around heavy machinery (such as excavators and cranes) on construction and industrial sites.

The project combines:
1. **Unity 3D Simulation & Digital Twin (`Blindspot AI`)**: High-fidelity 3D simulation replicating excavator kinematics, dynamic worker locomotion, vision frustums, and real-time hazard proximity warnings.
2. **Physical Sensor Fusion & AI Prototype (`BLINDSPOT PROJ`)**: Real-world hardware and computer vision pipeline combining **YOLOv8** object detection, **MiDaS** monocular depth estimation, ultrasonic distance sensors (**HC-SR04**), and **ESP32** wearable warning modules (haptic motors & buzzers).
3. **Research & Benchmarks**: IEEE research paper and empirical sensor-fusion benchmarks.

---

## 🏗️ Repository Architecture

```text
BLINDSPOT/
├── Blindspot AI/                       # Unity 3D Simulation Digital Twin
│   ├── Assets/
│   │   ├── Models/                     # 3D Excavator (Liebherr 956) & Worker GLB/FBX assets
│   │   ├── Prefabs/                    # Configured simulation prefabs
│   │   ├── Scenes/                     # Simulation environments & test scenes
│   │   ├── Scripts/                    # Kinematic controllers & safety zone logic
│   │   │   ├── AutoExcavatorWork.cs    # Automated excavator swing & dig routine
│   │   │   ├── BlindSpotDetector.cs    # Raycast & FOV proximity detection
│   │   │   ├── BlindSpotManager.cs     # Multi-zone hazard management
│   │   │   ├── ExcavatorArmController.cs
│   │   │   ├── ExcavatorController.cs
│   │   │   ├── ExcavatorRigController.cs
│   │   │   ├── WorkerController.cs     # Worker state machine
│   │   │   └── WorkerMovement.cs       # Autonomous worker patrol & pathing
│   │   └── TextMesh Pro/
│   ├── Packages/                       # Unity package dependencies
│   └── ProjectSettings/                # Input, physics, and graphics configurations
│
├── BLINDSPOT PROJ/                     # Hardware, Sensor Fusion & AI Pipeline
│   ├── SafeSightAi/                    # Integrated computer vision & safety suite
│   │   ├── config/                     # System & zone threshold YAML configs
│   │   ├── docs/                       # Architectural documentation & wiring diagrams
│   │   ├── firmware/                   # Microcontroller C/C++ firmware
│   │   ├── modules/                    # Depth, YOLO tracker, and safety zone modules
│   │   ├── scripts/                    # Calibration, camera verification, and tests
│   │   ├── live_safesight_fusion.py    # Main multi-modal sensor fusion runtime
│   │   └── requirements.txt            # Python dependencies
│   ├── blindspotai/                    # ESP32 Arduino firmware for ultrasonic + buzzers
│   ├── buzzer/                         # Standalone buzzer driver routines
│   ├── hcsr04_test/                    # Ultrasonic sensor verification
│   ├── check_all_hardware.py           # Automated peripheral self-test suite
│   ├── live_safesight_fusion.py        # Hardware-in-the-loop fusion script
│   ├── test_motor_alone.py             # Haptic vibration motor verification
│   ├── test_sensor_fusion_cases.py     # Deterministic fusion unit test suite
│   └── IEEE_Research_Paper_SafeSight_AI.md # Complete research publication manuscript
│
├── .gitignore                          # Clean repository filtering (Unity/Python/IDE/Binaries)
└── README.md                           # Project documentation
```

---

## 🚀 Getting Started

### 1. Unity 3D Simulation (`Blindspot AI`)
- **Requirements**: Unity Editor **6000.0.83f1 (Unity 6)** or compatible.
- **Open Project**:
  1. Open **Unity Hub**.
  2. Click **Add project from disk** and select the `Blindspot AI` folder.
  3. Launch the project using Unity 6000.0+.
  4. Open `Assets/Scenes/SampleScene.unity` to run the excavation site simulation.

### 2. Sensor Fusion & Vision Pipeline (`BLINDSPOT PROJ / SafeSightAi`)
- **Requirements**: Python 3.10+, USB Webcam, ESP32 Microcontroller.
- **Installation**:
  ```bash
  cd "BLINDSPOT PROJ/SafeSightAi"
  python -m venv venv
  # Windows:
  .\venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **Hardware Verification**:
  ```bash
  python check_all_hardware.py
  ```
- **Run Live Sensor Fusion**:
  ```bash
  python live_safesight_fusion.py
  ```

### 3. ESP32 Wearable Firmware
- Open `BLINDSPOT PROJ/blindspotai/blindspotai.ino` in the Arduino IDE or PlatformIO.
- Select board **ESP32 Dev Module**.
- Flash the firmware via USB to initialize the wearable worker safety band.

---

## 🔬 Research & Sensor Fusion Logic

The system categorizes hazards into three distinct zones based on fused depth perception and ultrasonic telemetry:
* 🟢 **Safe Zone (> 5.0m)**: Standard operational monitoring.
* 🟡 **Warning Zone (2.5m - 5.0m)**: Worker alerted via intermittent audible chime; operator HUD notification.
* 🔴 **Critical Hazard Zone (< 2.5m)**: Continuous haptic vibration, high-frequency alarm, and simulated equipment emergency stop (E-Stop).

For full theoretical derivation, mathematical sensor fusion models, and empirical testing data, refer to [`IEEE_Research_Paper_SafeSight_AI.md`](BLINDSPOT%20PROJ/IEEE_Research_Paper_SafeSight_AI.md).

---

## 📄 License & Attribution

Developed by the BlindSpot AI Team. Published to [`kkishore07/BLINDSPOT-PROJECT`](https://github.com/kkishore07/BLINDSPOT-PROJECT).
