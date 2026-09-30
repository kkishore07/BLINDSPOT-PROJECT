"""
SafeSight AI - Standalone Motor Controller / Test
Runs the L298N Motor Driver connected to ESP32 (GPIO 32 / 33) alone without activating the buzzer.
"""
import sys
import time
import json
import argparse
import serial

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORT = 'COM8'
BAUD = 74880  # ESP32 crystal-compensated baud rate (115200 * 26/40)

def connect_serial(port=PORT, baud=BAUD, timeout=1.0):
    print(f"🔌 Connecting to ESP32 on {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=timeout, dsrdtr=False, rtscts=False)
        ser.setDTR(False)
        ser.setRTS(False)
        time.sleep(1.5)
        # Flush startup garbage/heartbeats
        while ser.in_waiting:
            ser.readline()
        print(" Connected successfully.")
        return ser
    except Exception as e:
        print(f"❌ Failed to connect on {port}: {e}")
        return None

def run_motor_diagnostic_cycle(ser):
    """
    Sends the MOTOR command to trigger ESP32's built-in motor test:
    Forward (1.5s) -> Pause (0.3s) -> Reverse (1.5s) -> Stop.
    Buzzer remains completely silent.
    """
    print("\n" + "=" * 55)
    print(" 🚗 RUNNING MOTOR DIAGNOSTIC CYCLE (ALONE)")
    print("=" * 55)
    print("  Sending 'MOTOR' command to ESP32...")
    ser.write(b"MOTOR\n")
    ser.flush()

    start_time = time.time()
    # Expect cycle to take around 3.5 - 4 seconds
    while time.time() - start_time < 5.0:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                if "motor" in line.lower():
                    print(f"  ⚡ [MOTOR STATUS] {line}")
                elif "heartbeat" in line.lower() or "distance" in line.lower():
                    pass # suppress regular telemetry
                else:
                    print(f"  ESP32> {line}")
        time.sleep(0.05)

    print("✅ Motor diagnostic cycle completed.\n")

def run_motor_continuous(ser, duration_sec=5.0):
    """
    Runs the motor forward alone for a specified duration using JSON alert protocol
    with vibration=off and sound=off so buzzer remains completely silent.
    Keeps heartbeating every 1.0s to avoid the 3.0s safety watchdog timeout.
    """
    print("\n" + "=" * 55)
    print(f" 🚗 RUNNING MOTOR FORWARD ALONE FOR {duration_sec} SECONDS")
    print(" (Buzzer is explicitly silenced: sound=off, vibration=off)")
    print("=" * 55)

    alert_payload = json.dumps({
        "zone": "CRITICAL",
        "vibration": "off",
        "sound": "off",
        "worker_id": 99
    }) + "\n"

    safe_payload = json.dumps({
        "zone": "SAFE",
        "vibration": "off",
        "sound": "off"
    }) + "\n"

    print("  Starting motor (GPIO 32 HIGH, GPIO 33 LOW)...")
    ser.write(alert_payload.encode())
    ser.flush()

    start_time = time.time()
    last_refresh = time.time()

    try:
        while time.time() - start_time < duration_sec:
            elapsed = time.time() - start_time
            remaining = duration_sec - elapsed
            print(f"\r  ▶ Motor RUNNING... {elapsed:.1f}s / {duration_sec:.1f}s (Remaining: {remaining:.1f}s)", end="", flush=True)

            # Refresh every 1.5s to prevent watchdog timeout (3000ms)
            if time.time() - last_refresh >= 1.5:
                ser.write(alert_payload.encode())
                ser.flush()
                last_refresh = time.time()

            # Read any responses
            while ser.in_waiting:
                ser.readline()

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped early by user (Ctrl+C).")
    finally:
        print("\n  🛑 Stopping motor (Sending SAFE command)...")
        ser.write(safe_payload.encode())
        ser.flush()
        time.sleep(0.2)
        while ser.in_waiting:
            ser.readline()
        print("✅ Motor safely stopped.\n")

def run_motor_manual(ser):
    """
    Runs the motor forward alone continuously until the user presses Enter or Ctrl+C.
    """
    print("\n" + "=" * 55)
    print(" 🚗 RUNNING MOTOR ALONE (MANUAL CONTROL)")
    print(" (Buzzer is explicitly silenced: sound=off, vibration=off)")
    print(" Press ENTER at any time to STOP the motor.")
    print("=" * 55)

    alert_payload = json.dumps({
        "zone": "CRITICAL",
        "vibration": "off",
        "sound": "off",
        "worker_id": 99
    }) + "\n"

    safe_payload = json.dumps({
        "zone": "SAFE",
        "vibration": "off",
        "sound": "off"
    }) + "\n"

    import threading
    stop_event = threading.Event()

    def wait_for_enter():
        try:
            input("\n👉 Motor is ACTIVE. Press ENTER to stop...")
        except Exception:
            pass
        stop_event.set()

    t = threading.Thread(target=wait_for_enter, daemon=True)
    t.start()

    # Initial start
    ser.write(alert_payload.encode())
    ser.flush()
    start_time = time.time()
    last_refresh = time.time()

    try:
        while not stop_event.is_set():
            elapsed = time.time() - start_time
            print(f"\r  ▶ Motor RUNNING... {elapsed:.1f}s (Press Enter to stop)", end="", flush=True)

            # Prevent ESP32 3000ms watchdog timeout
            if time.time() - last_refresh >= 1.2:
                ser.write(alert_payload.encode())
                ser.flush()
                last_refresh = time.time()

            while ser.in_waiting:
                ser.readline()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped via Ctrl+C.")
    finally:
        ser.write(safe_payload.encode())
        ser.flush()
        time.sleep(0.2)
        while ser.in_waiting:
            ser.readline()
        print("\n✅ Motor safely stopped.\n")

def main():
    parser = argparse.ArgumentParser(description="Run the motor alone on SafeSight AI ESP32")
    parser.add_argument("--port", default=PORT, help=f"Serial COM port (default: {PORT})")
    parser.add_argument("--mode", choices=["cycle", "forward", "manual", "custom"], default="cycle",
                        help="Mode: 'cycle' (Forward 1.5s -> Pause -> Reverse 1.5s), 'forward' (Run forward alone for N seconds), 'manual' (Press Enter to stop)")
    parser.add_argument("--duration", type=float, default=4.0, help="Duration in seconds for forward mode (default: 4.0)")

    args = parser.parse_args()

    ser = connect_serial(args.port)
    if not ser:
        sys.exit(1)

    try:
        if args.mode == "cycle":
            run_motor_diagnostic_cycle(ser)
        elif args.mode == "forward":
            run_motor_continuous(ser, args.duration)
        elif args.mode == "manual":
            run_motor_manual(ser)
        elif args.mode == "custom":
            print("\nSafeSight AI - Motor Test Menu:")
            print("  1. Diagnostic Cycle (Forward 1.5s -> Pause -> Reverse 1.5s)")
            print("  2. Run Forward Alone (3 seconds)")
            print("  3. Run Forward Alone (6 seconds)")
            print("  4. Run Forward Alone (Continuous - Press Enter to Stop)")
            choice = input("Select an option [1-4]: ").strip()
            if choice == "1":
                run_motor_diagnostic_cycle(ser)
            elif choice == "2":
                run_motor_continuous(ser, 3.0)
            elif choice == "3":
                run_motor_continuous(ser, 6.0)
            elif choice == "4":
                run_motor_manual(ser)
            else:
                print("Invalid option. Running default diagnostic cycle.")
                run_motor_diagnostic_cycle(ser)
    finally:
        # Final safety check: always ensure SAFE is commanded before closing
        try:
            safe_payload = json.dumps({"zone": "SAFE", "vibration": "off", "sound": "off"}) + "\n"
            ser.write(safe_payload.encode())
            ser.flush()
            ser.close()
            print("🔒 Serial connection closed safely.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
