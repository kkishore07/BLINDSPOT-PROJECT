"""
SafeSight AI - Dynamic SG90 Servo Warning & Speed Controller
============================================================
Controls the SG90 Servo Motor on ESP32 Pin D33 based on Camera and Ultrasonic Sensors.

Behavior:
  1. Program Start -> Servo starts spinning continuously at Full Speed (100%).
  2. WARNING (Yellow) -> Speed reduces significantly (35% speed) as caution.
  3. DANGER  (Orange) -> Speed reduces further (15% speed crawl).
  4. CRITICAL (Red)   -> Servo STOPS COMPLETELY (0% Emergency Stop / E-Stop).
  5. Caution Cleared  -> Servo automatically resumes spinning at full speed!

Modes:
  1. Live Sensor Fusion Mode: Uses Camera (YOLO) + HC-SR04 Ultrasonic Sensor.
  2. Automated Demonstration Mode: Automatically cycles through all threat levels.
  3. Keyboard Interactive Mode: Manually trigger Safe / Warning / Red Stop / Clear.
"""

import sys
import os
import time
import json
import argparse
import serial
import serial.tools.list_ports

# Fix Windows console UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

current_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = current_dir if os.path.exists(os.path.join(current_dir, 'SafeSightAi')) else os.path.dirname(current_dir)
safesight_dir = os.path.join(current_dir, 'SafeSightAi')
if safesight_dir not in sys.path:
    sys.path.insert(0, safesight_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

DEFAULT_PORT = 'COM8'
DEFAULT_BAUD = 74880


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


def connect_esp32(port=None, baud=DEFAULT_BAUD):
    port = port or find_esp32_port()
    print(f"🔌 Connecting to ESP32 on {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=0.1, dsrdtr=False, rtscts=False)
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


def send_zone_command(ser, zone, worker_id=1):
    """
    Sends JSON alert matching SafeSight AI protocol to the ESP32.
    ESP32 firmware dynamically adjusts SG90 rotation speed and buzzer.
    """
    sound = "on" if zone in ["DANGER", "CRITICAL"] else "off"
    vibration = "continuous_high" if zone == "CRITICAL" else ("pulsed" if zone == "DANGER" else ("single_pulse" if zone == "WARNING" else "off"))

    payload = json.dumps({
        "zone": zone,
        "sound": sound,
        "vibration": vibration,
        "worker_id": worker_id
    }) + "\n"

    try:
        ser.write(payload.encode("utf-8"))
        ser.flush()
    except Exception as e:
        print(f"❌ Serial write error: {e}")


def read_esp32_telemetry(ser):
    """Reads any incoming status / distance telemetry from the ESP32."""
    dist = -1.0
    status = ""
    while ser.in_waiting:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("{"):
                data = json.loads(line)
                if "distance_cm" in data:
                    dist = float(data["distance_cm"])
                if "speed_state" in data:
                    status = data.get("speed_state", "")
        except Exception:
            pass
    return dist, status


def run_automated_demo(ser):
    """
    Demonstrates the complete sequence requested:
    1. Start -> Spinning at Full Speed (SAFE)
    2. Warning -> Speed reduces (WARNING)
    3. Red alert -> Stops completely (CRITICAL)
    4. Caution cleared -> Resumes spinning at Full Speed (SAFE)
    """
    print("\n" + "=" * 65)
    print(" 🎬 AUTOMATED SERVO ROTATION & SPEED DEMONSTRATION")
    print("=" * 65)

    stages = [
        ("SAFE", 5.0, "🟢 SAFE: Machinery in normal operation. Servo spinning at 100% full speed."),
        ("WARNING", 5.0, "🟡 WARNING: Worker approaching caution perimeter (20-50cm). Servo speed REDUCES to 35%."),
        ("DANGER", 4.0, "🟠 DANGER: Worker in close danger zone (10-20cm). Servo speed REDUCES to 15% crawl."),
        ("CRITICAL", 5.0, "🔴 CRITICAL / RED: Worker in immediate danger (<10cm). SERVO STOPS COMPLETELY (0% E-STOP)!"),
        ("SAFE", 6.0, "🟢 CAUTION CLEARED: Worker moved away to safe zone. SERVO RESUMES SPINNING AT FULL SPEED!")
    ]

    for zone, duration, desc in stages:
        print(f"\n▶ [{zone}] -> {desc}")
        send_zone_command(ser, zone)

        start = time.time()
        while time.time() - start < duration:
            dist, status = read_esp32_telemetry(ser)
            elapsed = time.time() - start
            rem = duration - elapsed
            speed_label = "100% SPEED" if zone == "SAFE" else ("35% SLOW" if zone == "WARNING" else ("15% CRAWL" if zone == "DANGER" else "STOPPED 0%"))
            dist_str = f"HC-SR04: {dist:.1f} cm" if dist > 0 else "HC-SR04: --"
            print(f"\r   Status: {speed_label:<15} | {dist_str:<18} | Time: {rem:.1f}s remaining...", end="", flush=True)
            time.sleep(0.2)
        print()

    print("\n✅ Automated demonstration completed.")


def run_keyboard_simulation(ser):
    """Interactive mode allowing instant keyboard toggling between threat zones."""
    print("\n" + "=" * 65)
    print(" 🎮 KEYBOARD SIMULATION MODE")
    print(" Controls:")
    print("   [1] or [S] -> SAFE (100% Full Speed Spinning)")
    print("   [2] or [W] -> WARNING (35% Reduced Caution Speed)")
    print("   [3] or [D] -> DANGER (15% Heavy Crawl Speed)")
    print("   [4] or [R] -> CRITICAL / RED (0% COMPLETE STOP - E-STOP)")
    print("   [C]        -> CAUTION CLEARED (Resume Full Speed Spinning)")
    print("   [Q]        -> Quit")
    print("=" * 65)

    current_state = "SAFE"
    send_zone_command(ser, "SAFE")

    while True:
        try:
            choice = input(f"\nCurrent State: [{current_state}] | Enter (1=Safe, 2=Warn, 3=Dang, 4=Red Stop, C=Clear, Q=Quit): ").strip().upper()
            if choice in ['Q', 'QUIT', 'EXIT']:
                print("Returning to SAFE and exiting...")
                send_zone_command(ser, "SAFE")
                break
            elif choice in ['1', 'S', 'C', 'CLEAR']:
                current_state = "SAFE"
                print("🟢 Action: Caution cleared -> Full Speed 100% Spinning")
                send_zone_command(ser, "SAFE")
            elif choice in ['2', 'W', 'WARN']:
                current_state = "WARNING"
                print("🟡 Action: Warning level -> Speed reduced to 35% caution")
                send_zone_command(ser, "WARNING")
            elif choice in ['3', 'D']:
                current_state = "DANGER"
                print("🟠 Action: Danger level -> Speed reduced to 15% crawl")
                send_zone_command(ser, "DANGER")
            elif choice in ['4', 'R', 'RED', 'STOP']:
                current_state = "CRITICAL"
                print("🔴 Action: RED WARNING! SERVO STOPS COMPLETELY (0% E-STOP)!")
                send_zone_command(ser, "CRITICAL")
            else:
                print("❌ Invalid command. Press 1, 2, 3, 4, C, or Q.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            send_zone_command(ser, "SAFE")
            break


def run_live_camera_fusion(ser):
    """Full live pipeline fusing Camera human detection + Ultrasonic distance with dynamic servo rotation."""
    import cv2

    print("\n" + "=" * 65)
    print(" 📷 LIVE CAMERA + ULTRASONIC SENSOR FUSION MODE")
    print("=" * 65)

    try:
        from modules.camera import WideAngleCamera
        from modules.detector import WorkerDetector
        from modules.sensor_fusion import SensorFusionEngine
    except ImportError as e:
        print(f"❌ Failed to load SafeSight AI modules: {e}")
        return

    # Initialize Camera
    print("  Initializing Camera...")
    cam = WideAngleCamera(index=1, width=640, height=480, fps=30)
    if not cam.open():
        cam = WideAngleCamera(index=0, width=640, height=480, fps=30)
        if not cam.open():
            print("  ❌ No camera available. Please connect a webcam.")
            return

    # Initialize YOLOv8
    print("  Loading YOLOv8 Human Detector...")
    model_path = os.path.join(safesight_dir, "yolov8n.pt")
    if not os.path.exists(model_path):
        model_path = "yolov8n.pt"
    detector = WorkerDetector(model_name=model_path, conf_threshold=0.5, iou_threshold=0.45)
    if not detector.load_model():
        print("  ❌ Could not load YOLOv8 model.")
        cam.release()
        return

    fusion = SensorFusionEngine(warning_threshold_cm=50.0, danger_threshold_cm=20.0, critical_threshold_cm=10.0)

    window_name = "SafeSight AI - Dynamic Servo Safety System"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 960, 720)

    print("\n✅ Live system running! Press 'q' in video window to exit.")
    last_sent_zone = None
    latest_distance = -1.0

    # Start servo spinning at 100% on start
    send_zone_command(ser, "SAFE")

    try:
        while True:
            ret, frame = cam.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Check ESP32 distance telemetry
            dist, _ = read_esp32_telemetry(ser)
            if dist > 0:
                latest_distance = dist

            # Detect humans
            detections = detector.detect_workers(frame)
            human_detected = len(detections) > 0

            # Evaluate fusion
            eval_res = fusion.evaluate(human_detected=human_detected, distance_cm=latest_distance)
            zone = eval_res["zone"]
            alarm_active = eval_res["alarm_active"]
            reason = eval_res["reason"]

            # Update ESP32 if zone changed
            if zone != last_sent_zone:
                last_sent_zone = zone
                send_zone_command(ser, zone)

            # Render HUD
            h, w = frame.shape[:2]
            ZONE_COLORS = {
                "SAFE": (0, 220, 0),       # Green
                "WARNING": (0, 215, 255),  # Yellow
                "DANGER": (0, 140, 255),   # Orange
                "CRITICAL": (0, 0, 255)    # Red
            }
            color = ZONE_COLORS.get(zone, (0, 220, 0))

            # Draw bounding boxes
            for det in detections:
                box = det["bbox"]
                cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), color, 2)
                cv2.putText(frame, f"WORKER {det['confidence']:.2f}", (box[0], max(20, box[1] - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Top HUD
            cv2.rectangle(frame, (0, 0), (w, 110), (25, 25, 25), -1)
            cv2.line(frame, (0, 110), (w, 110), color, 3)

            human_str = f"CAMERA: HUMAN DETECTED ({len(detections)})" if human_detected else "CAMERA: NO HUMAN"
            cv2.putText(frame, human_str, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0) if human_detected else (180, 180, 180), 2)

            dist_str = f"HC-SR04: {latest_distance:.1f} cm" if latest_distance > 0 else "HC-SR04: -- cm"
            cv2.putText(frame, dist_str, (420, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

            # Zone Line
            fused_text = f"ZONE: [{zone}] - {'ALARM ON' if alarm_active else 'ALARM OFF'}"
            cv2.putText(frame, fused_text, (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Servo Status Line
            SERVO_MAP = {
                "SAFE": ("SERVO D33: SPINNING AT 100% (NORMAL SPEED)", (0, 255, 0)),
                "WARNING": ("SERVO D33: REDUCED TO 35% SPEED (CAUTION)", (0, 215, 255)),
                "DANGER": ("SERVO D33: REDUCED TO 15% SPEED (CRAWL)", (0, 140, 255)),
                "CRITICAL": ("SERVO D33: EMERGENCY STOP - 0% (E-STOP)", (0, 0, 255))
            }
            servo_text, servo_col = SERVO_MAP.get(zone, ("SERVO: UNKNOWN", (200, 200, 200)))
            cv2.putText(frame, servo_text, (15, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.65, servo_col, 2)

            # Bottom reason bar
            cv2.rectangle(frame, (0, h - 35), (w, h), (20, 20, 20), -1)
            cv2.putText(frame, reason, (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        print("\nShutting down live camera...")
        send_zone_command(ser, "SAFE")
        cam.release()
        cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="SG90 Dynamic Speed Warning System on ESP32 D33")
    parser.add_argument("--port", type=str, default=DEFAULT_PORT, help="COM port (default: COM8)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help=f"Baud rate (default: {DEFAULT_BAUD})")
    parser.add_argument("--demo", action="store_true", help="Run automated demonstration cycle")
    parser.add_argument("--sim", action="store_true", help="Run keyboard simulation mode")
    parser.add_argument("--live", action="store_true", help="Run full live camera + ultrasonic sensor fusion")

    args = parser.parse_args()

    ser = connect_esp32(port=args.port, baud=args.baud)
    if not ser:
        sys.exit(1)

    try:
        if args.demo:
            run_automated_demo(ser)
        elif args.sim:
            run_keyboard_simulation(ser)
        elif args.live:
            run_live_camera_fusion(ser)
        else:
            print("\nSelect Mode:")
            print("  [1] Automated Demonstration (Safe -> Warning -> Red Stop -> Caution Cleared)")
            print("  [2] Live Camera (YOLO) + Ultrasonic Sensor Fusion")
            print("  [3] Keyboard Simulation (Keys: 1=Safe, 2=Warn, 3=Dang, 4=Red Stop, C=Clear)")
            print("  [4] Exit")

            choice = input("\nEnter choice (1-4) [Default: 1]: ").strip()
            if choice == "2":
                run_live_camera_fusion(ser)
            elif choice == "3":
                run_keyboard_simulation(ser)
            elif choice == "4":
                print("Exiting.")
            else:
                run_automated_demo(ser)
    finally:
        ser.close()
        print("🔌 Serial port closed.")


if __name__ == '__main__':
    main()
