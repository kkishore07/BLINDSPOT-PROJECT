#include <Arduino.h>

// ========================================================
// HC-SR04 Ultrasonic Sensor Standalone Test
// ========================================================
// Wire Connections:
//   HC-SR04 VCC   -> ESP32 VIN / 5V  (MUST be 5V, 3.3V is not enough)
//   HC-SR04 GND   -> ESP32 GND
//   HC-SR04 TRIG  -> ESP32 GPIO 25
//   HC-SR04 ECHO  -> ESP32 GPIO 26
// ========================================================

#define TRIG_PIN 25
#define ECHO_PIN 26

void setup() {
  // ESP32 with 26MHz crystal:
  // Serial.begin(115200) runs at 74880 baud on the PC Serial Monitor!
  Serial.begin(115200);
  delay(1500);

  Serial.println();
  Serial.println("========================================");
  Serial.println("   HC-SR04 Ultrasonic Sensor Test");
  Serial.println("========================================");
  Serial.print("TRIG Pin: GPIO "); Serial.println(TRIG_PIN);
  Serial.print("ECHO Pin: GPIO "); Serial.println(ECHO_PIN);
  Serial.println("----------------------------------------");
  Serial.println("If using Serial Monitor, set Baud to: 74880");
  Serial.println("========================================");
  Serial.println();

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  digitalWrite(TRIG_PIN, LOW);
  delay(50);
}

void loop() {
  // 1. Check initial state of ECHO pin before pulse
  int initialEcho = digitalRead(ECHO_PIN);

  // 2. Clear trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(4);

  // 3. Send a 10 microsecond HIGH pulse to trigger
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // 4. Measure duration of the echo pulse (timeout: 40000 us = ~6.8 meters)
  long duration = pulseIn(ECHO_PIN, HIGH, 40000);

  // 5. Output results with diagnostics
  if (duration == 0) {
    Serial.print("[FAIL] No Echo Received | Initial ECHO Pin State: ");
    if (initialEcho == HIGH) {
      Serial.println("HIGH (Warning: Echo pin is stuck HIGH. Check wiring/pullup)");
    } else {
      Serial.println("LOW");
      Serial.println("       Possible causes:");
      Serial.println("       1. Sensor VCC is on 3.3V instead of 5V/VIN (most common)");
      Serial.println("       2. TRIG & ECHO wires are swapped");
      Serial.println("       3. GND is disconnected");
    }
  } else {
    // Speed of sound = 343 m/s = 0.0343 cm/us -> distance = (duration * 0.0343) / 2
    float distanceCm = (duration / 2.0) / 29.1;
    float distanceInch = distanceCm / 2.54;

    Serial.print("[OK] Duration: ");
    Serial.print(duration);
    Serial.print(" us | Distance: ");
    Serial.print(distanceCm, 1);
    Serial.print(" cm (");
    Serial.print(distanceInch, 1);
    Serial.println(" in)");
  }

  delay(600);
}
