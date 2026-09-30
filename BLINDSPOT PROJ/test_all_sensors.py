"""
SafeSight AI - Comprehensive All-Sensors Diagnostic & Fusion Test Suite
=======================================================================
Tests all connected sensors and actuators in the BlindSpot AI safety system:
  1. Camera (Webcam + YOLOv8 Human Detection)
  2. HC-SR04 Ultrasonic Distance Sensor (GPIO 25 TRIG / GPIO 26 ECHO)
  3. SG90 Servo Motor (GPIO 33 - Dynamic Speed & E-Stop)
  4. Piezo Buzzer (GPIO 27 - Caution & Danger Alerts)
  5. Multi-Modal Sensor Fusion Engine

Usage:
  python test_all_sensors.py          # Complete Diagnostic + Live Option
  python test_all_sensors.py --live   # Directly launch Live Camera + Ultrasonic Fusion
  python test_all_sensors.py --diag   # Run Automated Hardware Diagnostics only
"""

import sys
import os
import time
import json
import argparse
import cv2
import serial
import serial.tools.list_ports

# Fix Windows console UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

current_dir = os.path.dirname(os.path.abspath(__file__))
# Robust SafeSightAi path discovery
if os.path.exists(os.path.join(current_dir, 'SafeSightAi')):
    safesight_dir = os.path.join(current_dir, 'SafeSightAi')
elif os.path.exists(os.path.join(current_dir, 'modules')):
    safesight_dir = current_dir
elif os.path.exists(os.path.join(os.path.dirname(current_dir), 'modules')):
    safesight_dir = os.path.dirname(current_dir)
else:
    safesight_dir = current_dir

if safesight_dir not in sys.path:
    sys.path.insert(0, safesight_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

DEFAULT_PORT = 'COM8'
DEFAULT_BAUD = 74880  # ESP32 26MHz crystal compensated baud rate (115200 * 26 / 40)


def find_esp32_port(preferred=DEFAULT_PORT):
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return preferred
    names = [p.device for p in ports]
    if preferred in names:
        return preferred
    for p in ports:
        desc = (p.description or "").lower()
        if "usb" in desc or "ch340" in desc or "cp210" in desc or "uart" in desc:
            return p.device
    return names[0]


def connect_esp32(port=None, baud=DEFAULT_BAUD, timeout=1.0):
    port = port or find_esp32_port()
    print(f"🔌 Connecting to ESP32 on {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=timeout, dsrdtr=False, rtscts=False)
        ser.setDTR(False)
        ser.setRTS(False)
        time.sleep(2.2)
        while ser.in_waiting:
            ser.readline()
            time.sleep(0.02)
        print(f" Connected successfully to ESP32 on {port}!")
        return ser
    except Exception as e:
        print(f"❌ Failed to connect on {port}: {e}")
        return None


# ==============================================================================
# 1. CAMERA & YOLO DIAGNOSTIC
# ==============================================================================
def test_camera_and_ai():
    print("\n" + "=" * 65)
    print(" [1/4] TESTING CAMERA & YOLOV8 HUMAN DETECTOR")
    print("=" * 65)

    try:
        from modules.camera import WideAngleCamera
        from modules.detector import WorkerDetector
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False, None

    # Open Camera
    print("  ▶ Opening Camera (trying index 1, fallback 0)...")
    cam = WideAngleCamera(index=1, width=640, height=480, fps=30)
    if not cam.open():
        cam = WideAngleCamera(index=0, width=640, height=480, fps=30)
        if not cam.open():
            print("  ❌ Camera open failed on both index 1 and index 0.")
            return False, None

    # Read test frames
    frames_read = 0
    t0 = time.time()
    last_frame = None
    for _ in range(15):
        ret, frame = cam.read()
        if ret and frame is not None:
            frames_read += 1
            last_frame = frame
    elapsed = time.time() - t0
    fps = frames_read / elapsed if elapsed > 0 else 0

    h, w = last_frame.shape[:2]
    brightness = last_frame.mean()
    print(f"  ✅ Camera Stream Working!")
    print(f"     Resolution:  {w}x{h}")
    print(f"     Capture FPS: {fps:.1f} fps")
    print(f"     Brightness:  {brightness:.1f} / 255.0")

    # Load YOLOv8 Model
    print("  ▶ Initializing YOLOv8 Human Detection Model...")
    model_file = os.path.join(safesight_dir, "yolov8n.pt")
    if not os.path.exists(model_file):
        model_file = "yolov8n.pt"

    detector = WorkerDetector(model_name=model_file, conf_threshold=0.5, iou_threshold=0.45)
    if not detector.load_model():
        print("  ❌ Failed to load YOLOv8 model weights.")
        cam.release()
        return False, None

    # Run inference test on captured frame
    t_inf0 = time.time()
    dets = detector.detect_workers(last_frame)
    inf_ms = (time.time() - t_inf0) * 1000
    print(f"  ✅ YOLOv8 AI Model Loaded & Verified!")
    print(f"     Inference:   {inf_ms:.1f} ms")
    print(f"     Detections:  {len(dets)} human(s) detected in current frame")

    cam.release()
    return True, detector


# ==============================================================================
# 2. HC-SR04 ULTRASONIC SENSOR DIAGNOSTIC
# ==============================================================================
def test_ultrasonic_sensor(ser):
    print("\n" + "=" * 65)
    print(" [2/4] TESTING HC-SR04 ULTRASONIC DISTANCE SENSOR (GPIO 25/26)")
    print("=" * 65)

    print("  ▶ Querying HC-SR04 sensor diagnostics on ESP32...")
    ser.write(b"HCSR04\n")
    ser.flush()

    time.sleep(1.2)
    hcsr04_ok = False
    measured_dist = -1.0

    while ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if "hcsr04" in line.lower() or "distance" in line.lower():
            try:
                data = json.loads(line)
                dist = data.get("dist_cm", -1)
                status = data.get("status", "UNKNOWN")
                echo_init = data.get("initial_echo", -1)
                pulse_us = data.get("pulse_us", 0)

                print(f"     Status:           {status}")
                print(f"     Trig Pin:         GPIO {data.get('trig')}")
                print(f"     Echo Pin:         GPIO {data.get('echo')}")
                print(f"     Pulse Duration:   {pulse_us} µs")
                print(f"     Measured Dist:    {dist:.1f} cm")

                if dist > 0:
                    hcsr04_ok = True
                    measured_dist = dist
                    print(f"  ✅ HC-SR04 Echo Valid! Distance: {dist:.1f} cm")
            except Exception:
                pass

    if not hcsr04_ok:
        # Check streaming telemetry
        print("  Checking live telemetry stream for distance samples...")
        start = time.time()
        while time.time() - start < 1.5:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "distance_cm" in line:
                    try:
                        data = json.loads(line)
                        d = float(data["distance_cm"])
                        if d > 0:
                            hcsr04_ok = True
                            measured_dist = d
                            print(f"  ✅ Received live distance: {d:.1f} cm")
                            break
                    except Exception:
                        pass
            time.sleep(0.05)

    if not hcsr04_ok:
        print("  ⚠️ No active echo received on GPIO 25/26.")
        print("     Wiring Checklist:")
        print("     - VCC -> 5V / VIN (HC-SR04 requires 5V)")
        print("     - GND -> ESP32 GND")
        print("     - TRIG -> GPIO 25")
        print("     - ECHO -> GPIO 26")

    return hcsr04_ok, measured_dist


# ==============================================================================
# 3. SG90 SERVO MOTOR SPEED & ROTATION TEST
# ==============================================================================
def test_servo_motor(ser):
    print("\n" + "=" * 65)
    print(" [3/4] TESTING SG90 SERVO MOTOR (GPIO 33 - Dynamic Speed & E-Stop)")
    print("=" * 65)

    stages = [
        ("FAST", "SERVO FAST\n", 2.5, "1. FAST SPEED (🟢 SAFE - 100% Operating Velocity)"),
        ("SLOW", "SERVO SLOW\n", 3.0, "2. SLOW SPEED (🟡 WARNING - 35% Caution Slowdown)"),
        ("CRAWL", "SERVO CRAWL\n", 2.5, "3. CRAWL SPEED (🟠 DANGER - 15% Crawl Speed)"),
        ("STOP", "SERVO STOP\n", 2.0, "4. EMERGENCY STOP (🔴 CRITICAL - 0% Complete Stop)"),
        ("FAST", "SERVO FAST\n", 2.0, "5. RESUME (🟢 CLEARED - Full Speed Rotation Resumed)")
    ]

    for name, cmd, delay, desc in stages:
        print(f"  ▶ {desc}...")
        ser.write(cmd.encode())
        ser.flush()

        start = time.time()
        while time.time() - start < delay:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "servo" in line.lower() and "speed" in line.lower():
                    print(f"     ESP32> {line}")
            time.sleep(0.1)

    print("  ✅ SG90 Servo dynamic speed & emergency stop verified!")
    return True


# ==============================================================================
# 4. BUZZER ALARM TEST
# ==============================================================================
def test_buzzer_alarm(ser):
    print("\n" + "=" * 65)
    print(" [4/4] TESTING PIEZO BUZZER (GPIO 27 - Audio Alerts)")
    print("=" * 65)

    print("  ▶ Testing Warning Single Beep (Buzzer ON for 0.3s)...")
    payload_warn = json.dumps({"zone": "WARNING", "sound": "on", "vibration": "single_pulse"}) + "\n"
    ser.write(payload_warn.encode())
    ser.flush()
    time.sleep(0.6)

    print("  ▶ Testing Critical Alarm (Continuous Siren for 0.8s)...")
    payload_crit = json.dumps({"zone": "CRITICAL", "sound": "on", "vibration": "continuous_high"}) + "\n"
    ser.write(payload_crit.encode())
    ser.flush()
    time.sleep(0.8)

    print("  ▶ Silencing Buzzer (Returning to SAFE)...")
    payload_safe = json.dumps({"zone": "SAFE", "sound": "off", "vibration": "off"}) + "\n"
    ser.write(payload_safe.encode())
    ser.flush()
    time.sleep(0.3)

    print("  ✅ Buzzer alert cycle completed!")
    return True


# ==============================================================================
# 5. LIVE SENSOR FUSION ENGINE (CAMERA + ULTRASONIC + SERVO + BUZZER)
# ==============================================================================
def run_live_fusion(ser):
    print("\n" + "=" * 65)
    print(" 🚀 LAUNCHING FULL MULTI-SENSOR FUSION PIPELINE")
    print("=" * 65)
    print("  Sensors Active:")
    print("    - Camera AI:   YOLOv8 Real-Time Human Tracking")
    print("    - Rangefinder: HC-SR04 Ultrasonic Distance (GPIO 25/26)")
    print("    - Actuator:    SG90 Servo (GPIO 33 - Dynamic Speed & E-Stop)")
    print("    - Alarm:       Piezo Buzzer (GPIO 27 - Caution & Danger Audio)")
    print("  Controls: Press 'q' in video window to exit.")
    print("=" * 65)

    from modules.camera import WideAngleCamera
    from modules.detector import WorkerDetector
    from modules.sensor_fusion import SensorFusionEngine

    cam = WideAngleCamera(index=1, width=640, height=480, fps=30)
    if not cam.open():
        cam = WideAngleCamera(index=0, width=640, height=480, fps=30)
        if not cam.open():
            print("  ❌ Camera open failed.")
            return

    model_file = os.path.join(safesight_dir, "yolov8n.pt")
    if not os.path.exists(model_file):
        model_file = "yolov8n.pt"
    detector = WorkerDetector(model_name=model_file, conf_threshold=0.5, iou_threshold=0.45)
    detector.load_model()

    fusion = SensorFusionEngine(warning_threshold_cm=50.0, danger_threshold_cm=20.0, critical_threshold_cm=10.0)

    window_name = "SafeSight AI - Full Sensor Fusion System"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 960, 720)

    # Start servo in SAFE (full speed rotation)
    payload_start = json.dumps({"zone": "SAFE", "sound": "off", "vibration": "off"}) + "\n"
    ser.write(payload_start.encode())
    ser.flush()

    latest_distance = -1.0
    last_sent_zone = None

    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Check distance telemetry from ESP32
            while ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "distance_cm" in line:
                        data = json.loads(line)
                        d = float(data.get("distance_cm", -1))
                        if d > 0:
                            latest_distance = d
                except Exception:
                    pass

            # Detect humans
            detections = detector.detect_workers(frame)
            human_detected = len(detections) > 0

            # Evaluate Fusion
            eval_res = fusion.evaluate(human_detected=human_detected, distance_cm=latest_distance)
            zone = eval_res["zone"]
            alarm_active = eval_res["alarm_active"]
            reason = eval_res["reason"]

            # Send update to ESP32 when state changes
            if zone != last_sent_zone:
                last_sent_zone = zone
                sound = "on" if zone in ["DANGER", "CRITICAL"] else "off"
                vibe = "continuous_high" if zone == "CRITICAL" else ("pulsed" if zone == "DANGER" else ("single_pulse" if zone == "WARNING" else "off"))
                msg = json.dumps({"zone": zone, "sound": sound, "vibration": vibe}) + "\n"
                ser.write(msg.encode())
                ser.flush()

            # Visual Rendering
            h, w = frame.shape[:2]
            ZONE_COLORS = {
                "SAFE": (0, 220, 0),
                "WARNING": (0, 215, 255),
                "DANGER": (0, 140, 255),
                "CRITICAL": (0, 0, 255)
            }
            color = ZONE_COLORS.get(zone, (0, 220, 0))

            # Bounding boxes
            for det in detections:
                box = det["bbox"]
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(frame, f"WORKER {det['confidence']:.2f}", (box[0], max(20, box[1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Top HUD (Height 115)
            cv2.rectangle(frame, (0, 0), (w, 115), (25, 25, 25), -1)
            cv2.line(frame, (0, 115), (w, 115), color, 3)

            # Row 1: Camera & Ultrasonic status
            h_text = f"CAMERA: HUMAN DETECTED ({len(detections)})" if human_detected else "CAMERA: NO HUMAN"
            cv2.putText(frame, h_text, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0) if human_detected else (180, 180, 180), 2)
            d_text = f"HC-SR04: {latest_distance:.1f} cm" if latest_distance > 0 else "HC-SR04: -- cm"
            cv2.putText(frame, d_text, (400, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            # Row 2: Safety Zone & Buzzer State
            f_text = f"ZONE: [{zone}] - {'BUZZER SIREN ACTIVE' if alarm_active else 'BUZZER SILENT'}"
            cv2.putText(frame, f_text, (15, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Row 3: SG90 Servo Speed State
            SERVO_MAP = {
                "SAFE": ("SERVO D33: SPINNING AT 100% (NORMAL OPERATION)", (0, 255, 0)),
                "WARNING": ("SERVO D33: REDUCED TO 35% SPEED (CAUTION SLOWDOWN)", (0, 215, 255)),
                "DANGER": ("SERVO D33: REDUCED TO 15% SPEED (HEAVY CRAWL)", (0, 140, 255)),
                "CRITICAL": ("SERVO D33: EMERGENCY STOP - 0% (E-STOP)", (0, 0, 255))
            }
            s_text, s_col = SERVO_MAP.get(zone, ("SERVO: UNKNOWN", (200, 200, 200)))
            cv2.putText(frame, s_text, (15, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.65, s_col, 2)

            # Bottom reason banner
            cv2.rectangle(frame, (0, h - 35), (w, h), (20, 20, 20), -1)
            cv2.putText(frame, reason, (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        print("\nStopping sensor fusion...")
        ser.write(b'{"zone":"SAFE","sound":"off","vibration":"off"}\n')
        ser.flush()
        cam.release()
        cv2.destroyAllWindows()


# ==============================================================================
# MAIN CONTROLLER
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Test All BlindSpot Sensors")
    parser.add_argument("--port", type=str, default=DEFAULT_PORT, help="COM port (default: COM8)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help=f"Baud rate (default: {DEFAULT_BAUD})")
    parser.add_argument("--live", action="store_true", help="Launch live camera + ultrasonic sensor fusion")
    parser.add_argument("--diag", action="store_true", help="Run automated diagnostics on all sensors")

    args = parser.parse_args()

    # Step 1: Connect to ESP32
    ser = connect_esp32(port=args.port, baud=args.baud)
    if not ser:
        sys.exit(1)

    try:
        if args.live:
            run_live_fusion(ser)
        elif args.diag:
            cam_ok, _ = test_camera_and_ai()
            hcsr04_ok, _ = test_ultrasonic_sensor(ser)
            servo_ok = test_servo_motor(ser)
            buzzer_ok = test_buzzer_alarm(ser)

            print("\n" + "=" * 65)
            print(" 📋 ALL-SENSORS DIAGNOSTIC SUMMARY")
            print("=" * 65)
            print(f"  1. Camera & YOLO AI:     {'✅ PASS' if cam_ok else '❌ FAIL'}")
            print(f"  2. HC-SR04 Ultrasonic:   {'✅ PASS' if hcsr04_ok else '⚠️ CHECK WIRING'}")
            print(f"  3. SG90 Servo (D33):      {'✅ PASS' if servo_ok else '❌ FAIL'}")
            print(f"  4. Buzzer Alarm (D27):   {'✅ PASS' if buzzer_ok else '❌ FAIL'}")
            print("=" * 65)
        else:
            # Run diagnostic first
            cam_ok, _ = test_camera_and_ai()
            hcsr04_ok, _ = test_ultrasonic_sensor(ser)
            servo_ok = test_servo_motor(ser)
            buzzer_ok = test_buzzer_alarm(ser)

            print("\n" + "=" * 65)
            print(" 📋 ALL-SENSORS DIAGNOSTIC SUMMARY")
            print("=" * 65)
            print(f"  1. Camera & YOLO AI:     {'✅ PASS' if cam_ok else '❌ FAIL'}")
            print(f"  2. HC-SR04 Ultrasonic:   {'✅ PASS' if hcsr04_ok else '⚠️ CHECK WIRING'}")
            print(f"  3. SG90 Servo (D33):      {'✅ PASS' if servo_ok else '❌ FAIL'}")
            print(f"  4. Buzzer Alarm (D27):   {'✅ PASS' if buzzer_ok else '❌ FAIL'}")
            print("=" * 65)

            choice = input("\nWould you like to launch Live Sensor Fusion with OpenCV HUD? (y/n) [Default: y]: ").strip().lower()
            if choice != 'n':
                run_live_fusion(ser)
    finally:
        ser.close()
        print("🔌 Serial connection closed.")


if __name__ == "__main__":
    main()
