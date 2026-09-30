import serial
import time
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORT = 'COM8'
BAUD = 74880  # For ESP32 with 26MHz crystal

print(f"Connecting to ESP32 on {PORT} at {BAUD} baud...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=1, dsrdtr=False, rtscts=False)
    ser.setDTR(False)
    ser.setRTS(False)
    print("Connected! Listening for HC-SR04 readings (Press Ctrl+C to stop)...")
    print("-" * 50)
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(line)
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\nStopped.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
