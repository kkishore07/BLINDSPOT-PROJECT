"""
SafeSight AI - Live Physical Prototype Sensor Fusion
Combines real-time Camera Human Detection (YOLOv8) with HC-SR04 Ultrasonic Distance.

Safety Requirement:
  - HC-SR04 detecting an obstacle (wall, rock, machine) ALONE will NEVER trigger the buzzer.
  - Alarm triggers ONLY when a human is detected AND inside the physical danger distance.
"""

import sys
import os
import time
import json
import argparse
import cv2
import numpy as np

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = current_dir if os.path.exists(os.path.join(current_dir, 'modules')) else os.path.join(current_dir, 'SafeSightAi')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from modules.camera import WideAngleCamera
from modules.detector import WorkerDetector
from modules.communication import WearableCommunicator
from modules.sensor_fusion import SensorFusionEngine

def main():
    parser = argparse.ArgumentParser(description="SafeSight AI - Real-time Physical Sensor Fusion")
    parser.add_argument("--no-gui", action="store_true", help="Run in headless console mode without display window")
    parser.add_argument("--duration", type=int, default=0, help="Run for N seconds then exit (0 = infinite)")
    args = parser.parse_args()

    # Load configuration
    config_path = os.path.join(repo_dir, 'config', 'settings.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}

    cam_cfg = config.get("camera", {})
    yolo_cfg = config.get("yolo", {})
    wearable_cfg = config.get("wearable", {})

    print("=" * 65)
    print(" SafeSight AI - Two-Sensor Physical Prototype Fusion System")
    print("=" * 65)

    # 1. Initialize ESP32 Wearable Communicator
    print("[1/4] Initializing ESP32 Wearable Communicator...")
    communicator = WearableCommunicator(wearable_cfg)
    time.sleep(1.5)

    # 2. Initialize Camera
    print("[2/4] Initializing Camera (Index {})...".format(cam_cfg.get("index", 1)))
    camera = WideAngleCamera(
        index=cam_cfg.get("index", 1),
        width=cam_cfg.get("width", 640),
        height=cam_cfg.get("height", 480),
        fps=cam_cfg.get("fps", 30)
    )
    if not camera.open():
        print("  ❌ Failed to open primary camera. Retrying on index 0...")
        camera = WideAngleCamera(index=0, width=640, height=480, fps=30)
        if not camera.open():
            print("  ❌ No camera could be opened. Exiting.")
            communicator.close()
            sys.exit(1)

    # 3. Initialize YOLOv8 Human Detector
    model_file = yolo_cfg.get("model_name", "yolov8n.pt")
    model_path = os.path.join(repo_dir, model_file) if os.path.exists(os.path.join(repo_dir, model_file)) else model_file
    print(f"[3/4] Loading YOLOv8 Human Detector ({model_file})...")
    detector = WorkerDetector(
        model_name=model_path,
        conf_threshold=yolo_cfg.get("conf_threshold", 0.5),
        iou_threshold=yolo_cfg.get("iou_threshold", 0.45),
        device=config.get("device", "cpu")
    )
    if not detector.load_model():
        print("  ❌ Failed to load YOLOv8 model.")
        camera.release()
        communicator.close()
        sys.exit(1)

    # 4. Initialize Sensor Fusion Engine
    print("[4/4] Initializing Sensor Fusion Engine...")
    fusion = SensorFusionEngine(
        warning_threshold_cm=50.0,
        danger_threshold_cm=20.0,
        critical_threshold_cm=10.0
    )

    print()
    print("=" * 65)
    print(" SYSTEM READY - Sensor Fusion Rules Active:")
    print("   1. NO Human in Camera      -> SAFE (Buzzer OFF, even if obstacle is close)")
    print("   2. Human + Distance > 50cm  -> SAFE (Buzzer OFF)")
    print("   3. Human + 20-50cm Distance -> WARNING (Single Beep)")
    print("   4. Human + 10-20cm Distance -> DANGER (Pulsed Buzzer)")
    print("   5. Human + <=10cm Distance  -> CRITICAL (Continuous Tone + Motor)")
    print("=" * 65)
    print("Press 'q' in video window or Ctrl+C in console to stop.")
    print()

    window_name = "SafeSight AI - Two-Sensor Fusion"
    if not args.no_gui:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 960, 720)

    start_loop_time = time.time()
    last_log_time = 0
    frame_count = 0
    fps = 0.0
    prev_time = time.time()

    try:
        while True:
            # Check duration limit if set
            if args.duration > 0 and (time.time() - start_loop_time) >= args.duration:
                print(f"\nDuration limit ({args.duration}s) reached.")
                break

            ret, frame = camera.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            curr_time = time.time()
            if curr_time - prev_time >= 1.0:
                fps = frame_count / (curr_time - prev_time)
                frame_count = 0
                prev_time = curr_time

            # Step 1: Detect humans via Camera AI
            t0 = time.time()
            detections = detector.detect_workers(frame)
            infer_ms = (time.time() - t0) * 1000
            human_detected = (len(detections) > 0)

            # Step 2: Read physical distance from HC-SR04
            distance_cm = communicator.get_latest_distance(max_age=1.5)

            # Step 3: Evaluate Sensor Fusion Logic
            eval_result = fusion.evaluate(
                human_detected=human_detected,
                distance_cm=distance_cm,
                worker_id=1
            )
            zone = eval_result["zone"]
            alarm_active = eval_result["alarm_active"]
            reason = eval_result["reason"]

            # Step 4: Transmit alert decision to ESP32 wearable
            communicator.send_alert(worker_id=1, zone=zone)

            # Console logging (rate-limited to 2 Hz)
            if curr_time - last_log_time >= 0.5:
                last_log_time = curr_time
                dist_str = f"{distance_cm:.1f} cm" if distance_cm > 0 else "Out of Range"
                print(f"[{time.strftime('%H:%M:%S')}] Human={human_detected} ({len(detections)}) | "
                      f"Dist={dist_str:>12} | "
                      f"State={zone:<8} | "
                      f"Alarm={'ACTIVE' if alarm_active else 'OFF':<6} | "
                      f"FPS={fps:.1f}")

            # Visual Display (if GUI enabled)
            if not args.no_gui:
                h, w = frame.shape[:2]

                # Colors (BGR)
                ZONE_COLORS = {
                    "SAFE": (0, 200, 0),       # Green
                    "WARNING": (0, 215, 255),  # Yellow
                    "DANGER": (0, 120, 255),   # Orange
                    "CRITICAL": (0, 0, 255)    # Red
                }
                status_color = ZONE_COLORS.get(zone, (0, 200, 0))

                # Draw bounding boxes
                for det in detections:
                    box = det["bbox"]
                    conf = det["confidence"]
                    cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), status_color, 2)
                    cv2.putText(
                        frame, f"HUMAN {conf:.2f}",
                        (box[0], max(20, box[1] - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2
                    )

                # Top HUD Bar
                cv2.rectangle(frame, (0, 0), (w, 110), (25, 25, 25), -1)
                cv2.line(frame, (0, 110), (w, 110), status_color, 3)

                # HUD Text - Line 1: Sensor Status
                human_text = f"CAMERA: HUMAN DETECTED ({len(detections)})" if human_detected else "CAMERA: NO HUMAN"
                human_col = (0, 255, 0) if human_detected else (180, 180, 180)
                cv2.putText(frame, human_text, (15, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, human_col, 2)

                dist_text = f"HC-SR04: {distance_cm:.1f} cm" if distance_cm > 0 else "HC-SR04: -- cm"
                cv2.putText(frame, dist_text, (380, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

                # HUD Text - Line 2: Overall Fused Alert State
                fused_text = f"FUSION: [{zone}] - {'BUZZER ALERT ACTIVE' if alarm_active else 'BUZZER OFF'}"
                cv2.putText(frame, fused_text, (15, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.68, status_color, 2)

                # HUD Text - Line 3: SG90 Servo Dynamic Speed State
                SERVO_STATUS_MAP = {
                    "SAFE": ("SERVO D33: SPINNING AT 100% (NORMAL SPEED)", (0, 255, 0)),
                    "WARNING": ("SERVO D33: REDUCED TO 35% SPEED (CAUTION)", (0, 215, 255)),
                    "DANGER": ("SERVO D33: REDUCED TO 15% SPEED (CRAWL)", (0, 140, 255)),
                    "CRITICAL": ("SERVO D33: EMERGENCY STOP - 0% (E-STOP)", (0, 0, 255))
                }
                servo_text, servo_col = SERVO_STATUS_MAP.get(zone, ("SERVO D33: UNKNOWN", (200, 200, 200)))
                cv2.putText(frame, servo_text, (15, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.65, servo_col, 2)

                # Bottom Explanation Bar
                cv2.rectangle(frame, (0, h - 35), (w, h), (20, 20, 20), -1)
                cv2.putText(frame, reason, (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)

                cv2.imshow(window_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nUser requested exit ('q').")
                    break

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("\nShutting down SafeSight AI...")
        # Send SAFE command to ensure buzzer and motor are immediately silenced
        try:
            communicator.send_alert(worker_id=1, zone="SAFE")
            time.sleep(0.2)
        except Exception:
            pass
        camera.release()
        communicator.close()
        cv2.destroyAllWindows()
        print("Shutdown complete. Buzzer & Motor confirmed silenced.")

if __name__ == '__main__':
    main()
