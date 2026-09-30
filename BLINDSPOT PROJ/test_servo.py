"""
SafeSight AI - Standalone SG90 Servo Motor Controller & Diagnostic Test
========================================================================
Controls the SG90 Servo Motor connected to ESP32 Pin D33 (GPIO 33).
Replaces the previous L298N DC motor driver.

Wiring:
  - SG90 Signal (Orange / Yellow) -> ESP32 D33 (GPIO 33)
  - SG90 VCC    (Red)             -> 5V / VIN
  - SG90 GND    (Brown / Black)   -> GND

Usage:
  python test_servo.py                # Interactive Menu
  python test_servo.py --angle 90     # Set immediate angle (0-180)
  python test_servo.py --sweep        # Run continuous back-and-forth sweep
  python test_servo.py --step-test    # Run stepped angle diagnostic
  python test_servo.py --zones        # Run SafeSight safety zone simulation
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

DEFAULT_PORT = 'COM8'
DEFAULT_BAUD = 74880  # ESP32 26MHz crystal compensated baud rate (115200 * 26 / 40)
ALT_BAUD = 115200


def find_esp32_port(preferred=DEFAULT_PORT):
    """Detects available serial ports and chooses the best match."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return preferred

    port_names = [p.device for p in ports]
    if preferred in port_names:
        return preferred

    for p in ports:
        desc = (p.description or "").lower()
        if "usb" in desc or "ch340" in desc or "cp210" in desc or "uart" in desc:
            return p.device

    return port_names[0]


def connect_esp32(port=None, baud=DEFAULT_BAUD, timeout=1.0):
    """Connects to the ESP32 on the specified COM port and baud rate."""
    if port is None:
        port = find_esp32_port()

    print(f"🔌 Connecting to ESP32 on {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=timeout, dsrdtr=False, rtscts=False)
        ser.setDTR(False)
        ser.setRTS(False)
        time.sleep(2.2)

        # Flush all initial boot banner messages
        while ser.in_waiting:
            ser.readline()
            time.sleep(0.05)

        print(f" Connected successfully on {port}!")
        return ser
    except Exception as e:
        print(f"❌ Failed to connect on {port}: {e}")
        if baud != ALT_BAUD:
            print(f"  Retrying on fallback baud {ALT_BAUD}...")
            try:
                ser = serial.Serial(port, ALT_BAUD, timeout=timeout, dsrdtr=False, rtscts=False)
                ser.setDTR(False)
                ser.setRTS(False)
                time.sleep(1.5)
                while ser.in_waiting:
                    ser.readline()
                print(f" Connected on {port} at {ALT_BAUD} baud!")
                return ser
            except Exception as e2:
                print(f"❌ Fallback failed: {e2}")
        return None


def send_servo_angle(ser, angle):
    """
    Sends an angle command to the ESP32 for the SG90 servo at GPIO 33.
    Accepts angle between 0 and 180 degrees.
    """
    angle = max(0, min(180, int(angle)))
    cmd = f"SERVO {angle}\n"
    ser.write(cmd.encode())
    ser.flush()

    # Read response
    start = time.time()
    resp = ""
    while time.time() - start < 0.5:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if "servo" in line.lower():
                resp = line
                break
        time.sleep(0.02)

    return resp


def run_stepped_angle_test(ser):
    """
    Diagnostic mode: moves the servo through reference angles:
    0° (Safe) -> 45° -> 90° (Center) -> 135° -> 180° (Max) -> 90° -> 0°
    """
    print("\n" + "=" * 60)
    print(" 🎯 SG90 SERVO STEPPED ANGLE DIAGNOSTIC (GPIO 33)")
    print("=" * 60)
    test_angles = [
        (0, "Safe / Retracted Position"),
        (45, "Low Warning Position"),
        (90, "Center / Deployed Hazard Barrier"),
        (135, "Extended Position"),
        (180, "Maximum Physical Rotation Limit"),
        (90, "Returning to Center (90°)"),
        (0, "Returning to Home / Safe (0°)")
    ]

    for angle, desc in test_angles:
        print(f"  ▶ Setting Angle: {angle:3d}° | {desc}...")
        resp = send_servo_angle(ser, angle)
        if resp:
            print(f"     ESP32> {resp}")
        time.sleep(1.0)

    print("\n✅ Stepped angle diagnostic completed successfully!\n")


def run_continuous_sweep(ser, cycles=3, step=5, delay=0.04):
    """
    Continuous Sweep Mode: Smoothly rotates between 0° and 180° back and forth.
    Like a radar sweep or physical safety barrier actuation.
    """
    print("\n" + "=" * 60)
    print(f" 🔄 SG90 SERVO CONTINUOUS SWEEP ({cycles} Cycles)")
    print(" Press Ctrl+C at any time to stop.")
    print("=" * 60)

    try:
        for cycle in range(1, cycles + 1):
            print(f"\n--- Cycle {cycle}/{cycles} ---")
            # Sweep forward: 0 -> 180
            for ang in range(0, 181, step):
                bar = "█" * (ang // 5) + "░" * ((180 - ang) // 5)
                print(f"\r  [0° -> 180°] Angle: {ang:3d}° |{bar}|", end="", flush=True)
                send_servo_angle(ser, ang)
                time.sleep(delay)

            # Sweep backward: 180 -> 0
            for ang in range(180, -1, -step):
                bar = "█" * (ang // 5) + "░" * ((180 - ang) // 5)
                print(f"\r  [180° -> 0°] Angle: {ang:3d}° |{bar}|", end="", flush=True)
                send_servo_angle(ser, ang)
                time.sleep(delay)

        # Return to safe 0°
        send_servo_angle(ser, 0)
        print("\n\n✅ Sweep completed. Servo returned to 0° (Home).")
    except KeyboardInterrupt:
        print("\n\n⚠️ Sweep interrupted by user. Returning servo to 0°...")
        send_servo_angle(ser, 0)


def run_safety_zone_simulation(ser):
    """
    Simulates the SafeSight AI Safety Zone Transitions:
      1. SAFE (0°)      -> Worker outside hazard range (servo retracted, buzzer off)
      2. WARNING (45°)   -> Worker entered caution zone (servo partially deployed, warning pulse)
      3. CRITICAL (90°)  -> Worker in blind spot danger (servo barrier deployed, continuous alarm)
      4. SAFE (0°)      -> Worker moved away
    """
    print("\n" + "=" * 60)
    print(" 🛡️ SAFESIGHT AI SAFETY ZONE SIMULATION WITH SG90 SERVO")
    print("=" * 60)

    scenarios = [
        {"zone": "SAFE", "servo": 0, "sound": "off", "vibration": "off", "duration": 3.0, "note": "Safe distance - Barrier retracted"},
        {"zone": "WARNING", "servo": 45, "sound": "on", "vibration": "pulsed", "duration": 4.0, "note": "Worker in caution zone (2.5m - 5.0m) - Caution flag deployed"},
        {"zone": "CRITICAL", "servo": 90, "sound": "on", "vibration": "continuous_high", "duration": 5.0, "note": "DANGER! Worker in blind spot (<2.5m) - Emergency barrier deployed"},
        {"zone": "SAFE", "servo": 0, "sound": "off", "vibration": "off", "duration": 2.0, "note": "Worker clear - Safety barrier retracted to 0°"}
    ]

    for sc in scenarios:
        print(f"\n  Zone: [{sc['zone']}] -> Angle: {sc['servo']}°")
        print(f"  Description: {sc['note']}")

        payload = json.dumps({
            "zone": sc["zone"],
            "servo": sc["servo"],
            "sound": sc["sound"],
            "vibration": sc["vibration"],
            "worker_id": 101
        }) + "\n"

        ser.write(payload.encode())
        ser.flush()

        start = time.time()
        while time.time() - start < sc["duration"]:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if "telemetry" in line:
                    pass  # skip raw distance lines
                elif line:
                    print(f"    ESP32> {line}")
            time.sleep(0.1)

    print("\n✅ Safety Zone simulation completed.")


def run_interactive_mode(ser):
    """Allows typing angles interactively from the keyboard."""
    print("\n" + "=" * 60)
    print(" 🎮 INTERACTIVE SG90 SERVO CONTROLLER (GPIO 33)")
    print(" Commands:")
    print("   0 - 180   : Move servo directly to that angle (e.g. 0, 45, 90, 180)")
    print("   s / sweep : Run continuous sweep")
    print("   d / diag  : Run stepped diagnostic")
    print("   z / zone  : Run safety zone simulation")
    print("   q         : Quit to exit")
    print("=" * 60)

    while True:
        try:
            cmd = input("\nEnter angle (0-180) or command: ").strip().lower()
            if not cmd or cmd == 'q' or cmd == 'quit' or cmd == 'exit':
                print("Exiting interactive mode...")
                send_servo_angle(ser, 0)
                break
            elif cmd in ['s', 'sweep']:
                run_continuous_sweep(ser, cycles=2)
            elif cmd in ['d', 'diag']:
                run_stepped_angle_test(ser)
            elif cmd in ['z', 'zone']:
                run_safety_zone_simulation(ser)
            else:
                try:
                    angle = int(cmd)
                    if 0 <= angle <= 180:
                        resp = send_servo_angle(ser, angle)
                        print(f"  ▶ Servo set to {angle}° | {resp}")
                    else:
                        print("  ❌ Angle must be between 0 and 180 degrees.")
                except ValueError:
                    print("  ❌ Invalid input. Enter a number 0-180, 'sweep', 'diag', or 'q'.")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            send_servo_angle(ser, 0)
            break


def main():
    parser = argparse.ArgumentParser(description="Test SG90 Servo Motor on ESP32 D33")
    parser.add_argument("--port", type=str, default=DEFAULT_PORT, help="Serial port (default: COM8)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help=f"Baud rate (default: {DEFAULT_BAUD})")
    parser.add_argument("--angle", type=int, default=None, help="Set specific angle (0-180) and exit")
    parser.add_argument("--sweep", action="store_true", help="Run continuous back-and-forth sweep")
    parser.add_argument("--step-test", action="store_true", help="Run stepped angle diagnostic (0-180)")
    parser.add_argument("--zones", action="store_true", help="Simulate SafeSight AI safety zones")
    parser.add_argument("--cycles", type=int, default=3, help="Number of sweep cycles (default: 3)")

    args = parser.parse_args()

    port = args.port or find_esp32_port()
    ser = connect_esp32(port=port, baud=args.baud)
    if not ser:
        sys.exit(1)

    try:
        if args.angle is not None:
            print(f"Setting servo angle to {args.angle}°...")
            resp = send_servo_angle(ser, args.angle)
            print(f"Result: {resp}")
            time.sleep(0.5)
        elif args.sweep:
            run_continuous_sweep(ser, cycles=args.cycles)
        elif args.step_test:
            run_stepped_angle_test(ser)
        elif args.zones:
            run_safety_zone_simulation(ser)
        else:
            # Interactive Menu
            print("\nSelect Test Mode:")
            print("  [1] Stepped Angle Diagnostic (0° -> 45° -> 90° -> 135° -> 180° -> 0°)")
            print("  [2] Continuous Radar / Barrier Sweep (Smooth 0° <-> 180°)")
            print("  [3] SafeSight AI Safety Zone Simulation (SAFE / WARNING / CRITICAL)")
            print("  [4] Interactive Manual Angle Control")
            print("  [5] Exit")

            choice = input("\nEnter choice (1-5) [Default: 1]: ").strip()
            if choice == "2":
                run_continuous_sweep(ser, cycles=args.cycles)
            elif choice == "3":
                run_safety_zone_simulation(ser)
            elif choice == "4":
                run_interactive_mode(ser)
            elif choice == "5":
                print("Exiting.")
            else:
                run_stepped_angle_test(ser)
    finally:
        ser.close()
        print("🔌 Serial port closed.")


if __name__ == "__main__":
    main()
