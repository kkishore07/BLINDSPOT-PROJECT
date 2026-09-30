# SafeSight AI 🛡️

**Intelligent Blind Spot & Hazard Mitigation System for Heavy Industrial Equipment**

SafeSight AI is a multi-modal safety solution combining real-time computer vision (YOLOv8 + MiDaS depth estimation) and physical proximity sensing (HC-SR04 Ultrasonic) with wearable alert devices (ESP32) to prevent heavy machinery collisions with workers in industrial and mining environments.

---

## 🌟 Key Features

- **Multi-Sensor Fusion Architecture**:
  - **Vision-First Safety Rule**: Ultrasonic detections alone (walls, rocks, inanimate machinery) *never* trigger false buzzer alarms.
  - **Human Threat Escalation**: Alarms activate exclusively when computer vision confirms human presence inside configurable proximity zones.
- **Real-Time Human Detection**: Powered by lightweight YOLOv8 models (`yolov8n.pt`) with real-time bounding box tracking.
- **Physical Wearable Feedback**:
  - ESP32 microcontroller with active buzzer and vibration motor (L298N driver).
  - Multi-tier alert levels: `SAFE`, `WARNING` (single beep), `DANGER` (pulsed buzzer), and `CRITICAL` (continuous alarm + haptic vibration).
  - Multi-channel communication: Serial USB (74880 baud for 26MHz XTAL ESP32) and local UDP loopback.
- **Comprehensive Hardware Diagnostics**: Dedicated self-tests for camera, HC-SR04, motors, and buzzer.

---

## 📐 Sensor Fusion Threat Matrix

| Condition | Camera Human Detected | HC-SR04 Distance | Zone | Alarm & Alert State |
| :--- | :---: | :---: | :---: | :--- |
| **No Person (Obstacle Only)** | ❌ No | Any (e.g. 5 cm) | `SAFE` | Buzzer OFF (Suppressed) |
| **Worker Far Away** | ✅ Yes | > 50 cm | `SAFE` | Buzzer OFF |
| **Worker In Warning Range** | ✅ Yes | 20 cm – 50 cm | `WARNING` | Single Warning Beep |
| **Worker In Danger Zone** | ✅ Yes | 10 cm – 20 cm | `DANGER` | Pulsed Buzzer Alert |
| **Worker In Critical Proximity**| ✅ Yes | $\le$ 10 cm | `CRITICAL` | Continuous Alarm + Motor |

---

## 📂 Project Structure

```
SafeSightAi/
├── config/
│   ├── calibration_profiles.json   # Physical depth calibration
│   └── settings.json               # Camera, YOLO, and ESP32 wearable config
├── docs/
│   └── IEEE_Research_Paper_SafeSight_AI.md  # Comprehensive research paper
├── firmware/
│   ├── esp32_wearable/             # Main ESP32 firmware & Wokwi simulation
│   │   ├── blindspotai.ino
│   │   ├── diagram.json
│   │   └── wokwi.toml
│   ├── hcsr04_test/                # HC-SR04 test sketch
│   └── buzzer/                     # Buzzer test sketch
├── modules/
│   ├── alert_decision.py           # Multi-worker threat state machine
│   ├── camera.py                   # Wide-angle camera feed with DirectShow fallback
│   ├── communication.py            # Serial (USB) and UDP wearable communicator
│   ├── depth.py                    # MiDaS monocular depth estimation
│   ├── detector.py                 # YOLOv8 worker detection
│   ├── proximity.py                # Visual distance estimation
│   ├── safety.py                   # Dynamic safety zone thresholds
│   ├── sensor_fusion.py            # Two-sensor fusion engine
│   └── tracking.py                 # ByteTrack multi-object tracking
├── scripts/
│   ├── calibration_tool.py         # Interactive depth calibration GUI
│   ├── read_hcsr04.py              # Serial ultrasonic monitor
│   ├── test_buzzer.py              # Buzzer standalone test
│   ├── test_motor_alone.py         # Motor driver standalone test
│   ├── verify_alert_decision.py    # Alert unit tests
│   ├── verify_midas.py             # MiDaS pipeline validation
│   ├── verify_pipeline.py          # Vision pipeline verification
│   └── verify_yolo.py              # YOLO detection verification
├── live_safesight_fusion.py        # Main real-time sensor fusion prototype runner
├── test_sensor_fusion_cases.py     # 7-case sensor fusion verification suite
├── check_all_hardware.py           # Full hardware diagnostic tool
├── test_esp32.py                   # ESP32 serial communication validation
└── requirements.txt                # Python dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites & Installation

```bash
git clone https://github.com/jayasuriyajs3/SafeSightAI.git
cd SafeSightAI

# Install dependencies
pip install -r requirements.txt
```

### 2. Hardware Diagnostics

Run the integrated diagnostic suite to verify connected hardware (Camera, HC-SR04, ESP32, Buzzer):

```bash
python check_all_hardware.py
```

### 3. Run Sensor Fusion Verification Tests

Validate the 7 core safety logic test cases:

```bash
python test_sensor_fusion_cases.py
```

### 4. Launch Live Prototype

Run the live two-sensor fusion system with real-time video overlay and ESP32 telemetry:

```bash
python live_safesight_fusion.py
```

*Options:*
- `--no-gui`: Run in headless mode without display window.
- `--duration N`: Run for $N$ seconds then exit cleanly.

---

## 🔌 Hardware Setup & Wiring

- **Microcontroller**: ESP32 (30-pin / 38-pin DevKit)
- **Ultrasonic Sensor**: HC-SR04 (`TRIG` $\rightarrow$ GPIO 25, `ECHO` $\rightarrow$ GPIO 26 via voltage divider)
- **Active Buzzer**: GPIO 27
- **Haptic/Motor Driver**: L298N (`IN1` $\rightarrow$ GPIO 32, `IN2` $\rightarrow$ GPIO 33)
- **Baud Rate**: 74880 baud (ESP32 26MHz crystal bootloader & runtime) or 115200 baud.

Flash firmware from `firmware/esp32_wearable/blindspotai.ino` using the Arduino IDE or PlatformIO.

---

## 📄 License & Attribution

Developed for industrial workplace safety and blind-spot mitigation. See [IEEE Research Paper](docs/IEEE_Research_Paper_SafeSight_AI.md) for theoretical foundation, experimental results, and architectural benchmarks.
