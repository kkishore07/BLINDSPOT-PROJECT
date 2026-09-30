import serial
import time
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORT = 'COM8'
BAUD = 74880  # 26MHz XTAL ESP32: 115200 * 26/40 = 74880

print(f"Connecting to ESP32 on {PORT} at {BAUD} baud...")
ser = serial.Serial(PORT, BAUD, timeout=1, dsrdtr=False, rtscts=False)
ser.setDTR(False)
ser.setRTS(False)

print("Connected! Waiting 2 seconds for boot messages...")
time.sleep(2)
while ser.in_waiting:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"  ESP32> {line}")

# Test 1: Single Pulse (WARNING)
print("\n[1] Beep Test: Single pulse (WARNING)...")
cmd = json.dumps({"zone": "WARNING", "vibration": "single_pulse", "sound": "off"}) + "\n"
ser.write(cmd.encode())
ser.flush()
time.sleep(1)
while ser.in_waiting:
    print(f"  ESP32> {ser.readline().decode('utf-8', errors='ignore').strip()}")

# Test 2: Pulsed Beeps (DANGER) for 3 seconds
print("\n[2] Beep Test: Pulsed rapid beeps (DANGER) for 3 seconds...")
cmd = json.dumps({"zone": "DANGER", "vibration": "pulsed", "sound": "off"}) + "\n"
ser.write(cmd.encode())
ser.flush()
for _ in range(6):
    time.sleep(0.5)
    while ser.in_waiting:
        print(f"  ESP32> {ser.readline().decode('utf-8', errors='ignore').strip()}")

# Test 3: Continuous Beep (CRITICAL) for 2 seconds
print("\n[3] Beep Test: Continuous tone (CRITICAL) for 2 seconds...")
cmd = json.dumps({"zone": "CRITICAL", "vibration": "continuous_high", "sound": "on"}) + "\n"
ser.write(cmd.encode())
ser.flush()
time.sleep(2)
while ser.in_waiting:
    print(f"  ESP32> {ser.readline().decode('utf-8', errors='ignore').strip()}")

# Test 4: Reset to SAFE (Silence)
print("\n[4] Resetting to SAFE (Silence)...")
cmd = json.dumps({"zone": "SAFE", "vibration": "off", "sound": "off"}) + "\n"
ser.write(cmd.encode())
ser.flush()
time.sleep(0.5)
while ser.in_waiting:
    print(f"  ESP32> {ser.readline().decode('utf-8', errors='ignore').strip()}")

ser.close()
print("\nBuzzer test completed successfully!")
