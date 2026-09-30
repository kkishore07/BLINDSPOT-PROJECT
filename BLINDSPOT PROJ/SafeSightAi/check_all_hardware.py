"""
SafeSight AI - Full Hardware Diagnostics
Checks Camera, HC-SR04 Ultrasonic Sensor, L298N Motor Driver, and Buzzer.
"""
import sys
import os
import time
import json
import cv2

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
current_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = current_dir if os.path.exists(os.path.join(current_dir, 'modules')) else os.path.join(current_dir, 'SafeSightAi')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

import serial
from modules.camera import WideAngleCamera

def check_camera():
    print("=" * 50)
    print(" [1/3] CHECKING CAMERA")
    print("=" * 50)
    cam = WideAngleCamera(index=1, width=640, height=480, fps=30)
    if not cam.open():
        print("  ❌ Camera open failed on index 1. Trying index 0...")
        cam = WideAngleCamera(index=0, width=640, height=480, fps=30)
        if not cam.open():
            print("  ❌ No camera could be opened.")
            return False

    frames_read = 0
    start_time = time.time()
    for _ in range(10):
        ret, frame = cam.read()
        if ret and frame is not None:
            frames_read += 1
    elapsed = time.time() - start_time
    fps = frames_read / elapsed if elapsed > 0 else 0

    h, w, c = frame.shape
    mean_brightness = frame.mean()
    cam.release()

    print(f"  ✅ Camera working!")
    print(f"     Resolution:  {w}x{h} ({c} channels)")
    print(f"     FPS:         {fps:.1f} fps")
    print(f"     Brightness:  {mean_brightness:.1f} (0-255 scale)")
    return True

def check_esp32_hardware():
    print()
    print("=" * 50)
    print(" [2/3] CHECKING HC-SR04 ULTRASONIC SENSOR")
    print("=" * 50)

    PORT = 'COM8'
    BAUD = 74880

    try:
        ser = serial.Serial(PORT, BAUD, timeout=2, dsrdtr=False, rtscts=False)
        ser.setDTR(False)
        ser.setRTS(False)
    except Exception as e:
        print(f"  ❌ Failed to open {PORT}: {e}")
        return False, False

    time.sleep(2)
    while ser.in_waiting:
        ser.readline()

    # Query HC-SR04
    print("  Sending HC-SR04 diagnostic ping...")
    ser.write(b"HCSR04\n")
    ser.flush()
    time.sleep(1)

    hcsr04_ok = False
    while ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if "hcsr04" in line:
            print(f"  ESP32 Response: {line}")
            try:
                data = json.loads(line)
                dist = data.get("dist_cm", -1)
                status = data.get("status", "UNKNOWN")
                echo_init = data.get("initial_echo", -1)
                pulse_us = data.get("pulse_us", 0)

                print(f"     Status:           {status}")
                print(f"     Trigger Pin:      GPIO {data.get('trig')}")
                print(f"     Echo Pin:         GPIO {data.get('echo')}")
                print(f"     Initial Echo:     {'HIGH (stuck?)' if echo_init == 1 else 'LOW (normal)'}")
                print(f"     Pulse Duration:   {pulse_us} us")
                print(f"     Measured Dist:    {dist} cm")

                if status == "OK" and dist > 0:
                    hcsr04_ok = True
                    print("  ✅ HC-SR04 is working and measuring distance!")
                elif status == "PINS_SWAPPED":
                    print(f"  ⚠️ PINS APPEAR SWAPPED! Suggested Trig: GPIO {data.get('suggested_trig')}, Echo: GPIO {data.get('suggested_echo')}")
                elif echo_init == 1:
                    print("  ⚠️ Echo pin is stuck HIGH. Check if Echo wire is shorted to 5V or pullup.")
                else:
                    print("  ⚠️ No echo received on GPIO 25/26. Scanning other common GPIO pin pairs...")
                    ser.write(b"SCAN_PINS\n")
                    ser.flush()
                    time.sleep(1.5)
                    while ser.in_waiting:
                        scan_line = ser.readline().decode('utf-8', errors='ignore').strip()
                        if "FOUND" in scan_line:
                            print(f"  🎉 ESP32 Scan: {scan_line}")
                            hcsr04_ok = True
                        elif "NOT_FOUND" in scan_line:
                            print(f"  ESP32 Scan: {scan_line}")
                    if not hcsr04_ok:
                        print("     Checklist:")
                        print("     1. Is HC-SR04 VCC connected to 5V (VIN)? (HC-SR04 does NOT work reliably on 3.3V)")
                        print("     2. Are TRIG and ECHO wires firmly seated in the breadboard / header?")
                        print("     3. Is GND connected to ESP32 GND?")
            except Exception as e:
                print(f"  Parse error: {e}")

    # Motor Test
    print()
    print("=" * 50)
    print(" [3/3] CHECKING MOTOR (L298N on GPIO 32 / 33)")
    print("=" * 50)
    print("  Triggering motor test (Forward 1.5s -> Pause -> Reverse 1.5s)...")
    ser.write(b"MOTOR\n")
    ser.flush()

    motor_ok = True
    start = time.time()
    while time.time() - start < 5:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"  ESP32> {line}")
        time.sleep(0.1)

    ser.close()
    return True, hcsr04_ok

if __name__ == '__main__':
    print("**************************************************")
    print(" SafeSight AI - Hardware Verification Suite")
    print("**************************************************")
    print()

    cam_ok = check_camera()
    esp_ok, hcsr04_ok = check_esp32_hardware()

    print()
    print("=" * 50)
    print(" DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"  Camera:   {'✅ PASS' if cam_ok else '❌ FAIL'}")
    print(f"  HC-SR04:  {'✅ PASS' if hcsr04_ok else '⚠️ NEEDS WIRING CHECK'}")
    print(f"  Motor:    {'✅ TEST COMPLETED' if esp_ok else '❌ PORT ERROR'}")
    print("=" * 50)
