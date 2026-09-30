"""
SafeSight AI - ESP32 Serial Communication Test
Tests the full alert pipeline over USB Serial.
"""
import serial
import time
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 26MHz XTAL ESP32: actual baud = 115200 * 26/40 = 74880
BAUD_RATE = 74880
PORT = 'COM8'

print(f"=== SafeSight AI - ESP32 Serial Test ===")
print(f"Port: {PORT} | Baud: {BAUD_RATE}")
print()

ser = serial.Serial(PORT, BAUD_RATE, timeout=1, dsrdtr=False, rtscts=False)
ser.setDTR(False)
ser.setRTS(False)

# Wait for ESP32 to boot and read startup messages
print("[1/5] Reading ESP32 startup messages...")
time.sleep(3)
while ser.in_waiting:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"  ESP32> {line}")

# Test 1: Send WARNING alert
print()
print("[2/5] Sending WARNING alert (single_pulse buzzer)...")
warning = json.dumps({
    "worker_id": 1,
    "zone": "WARNING",
    "vibration": "single_pulse",
    "light": "off",
    "sound": "off"
})
ser.write((warning + '\n').encode())
ser.flush()
time.sleep(1)
while ser.in_waiting:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"  ESP32> {line}")

# Test 2: Send DANGER alert
print()
print("[3/5] Sending DANGER alert (pulsed buzzer for 3 seconds)...")
danger = json.dumps({
    "worker_id": 1,
    "zone": "DANGER",
    "vibration": "pulsed",
    "light": "flashing",
    "sound": "off"
})
ser.write((danger + '\n').encode())
ser.flush()
time.sleep(3)
while ser.in_waiting:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"  ESP32> {line}")

# Test 3: Send CRITICAL alert
print()
print("[4/5] Sending CRITICAL alert (continuous buzzer + motor for 2 seconds)...")
critical = json.dumps({
    "worker_id": 1,
    "zone": "CRITICAL",
    "vibration": "continuous_high",
    "light": "flashing_red",
    "sound": "on"
})
ser.write((critical + '\n').encode())
ser.flush()
time.sleep(2)
while ser.in_waiting:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"  ESP32> {line}")

# Test 4: Send SAFE to stop everything
print()
print("[5/5] Sending SAFE (stop all alerts)...")
safe = json.dumps({
    "worker_id": 1,
    "zone": "SAFE",
    "vibration": "off",
    "light": "off",
    "sound": "off"
})
ser.write((safe + '\n').encode())
ser.flush()
time.sleep(1)
while ser.in_waiting:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"  ESP32> {line}")

# Wait for heartbeat
print()
print("Waiting for heartbeat...")
start = time.time()
while time.time() - start < 8:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if line:
        print(f"  ESP32> {line}")
        if "heartbeat" in line:
            break

ser.close()
print()
print("=== Test Complete ===")