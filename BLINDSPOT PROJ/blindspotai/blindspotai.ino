#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ========================
// Hardware Pin Mapping
// ========================
#define BUZZER_PIN      27   // Buzzer on GPIO 27
#define ULTRASONIC_TRIG 25   // HC-SR04 Trigger
#define ULTRASONIC_ECHO 26  // HC-SR04 Echo
#define SERVO_PIN       33   // SG90 Servo Signal on GPIO 33

// ========================
// Servo Controller
// ========================
Servo sg90Servo;
int currentServoAngle = 0;

// ========================
// Alert State
// ========================
String currentZone = "SAFE";
String vibrationMode = "off";
String soundMode = "off";
unsigned long lastAlertTime = 0;
const unsigned long ALERT_TIMEOUT_MS = 3000; // Return to SAFE if no alert for 3s

// Buzzer timing
unsigned long lastBuzzerToggle = 0;
bool buzzerState = false;

// Single pulse tracking
bool singlePulseActive = false;
unsigned long singlePulseStart = 0;
const unsigned long SINGLE_PULSE_DURATION = 200; // ms

// Heartbeat
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 5000; // 5s

// Serial input buffer
String serialBuffer = "";

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("========================================");
  Serial.println("  SafeSight AI - ESP32 Wearable Alert");
  Serial.println("  Mode: Serial (USB) Communication");
  Serial.println("========================================");

  // Setup pins
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);

  // Setup SG90 Servo on GPIO 33
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  sg90Servo.setPeriodHertz(50);           // Standard 50Hz servo
  sg90Servo.attach(SERVO_PIN, 500, 2400);  // SG90 standard pulse widths (500us to 2400us)
  sg90Servo.write(0);                     // Default position: 0 degrees (SAFE)

  Serial.println("[Init] Buzzer on GPIO 27");
  Serial.println("[Init] Ultrasonic on GPIO 25/26");
  Serial.println("[Init] SG90 Servo on GPIO 33");
  Serial.println();
  Serial.println("========================================");
  Serial.println("  READY - Send JSON alerts or SERVO commands via Serial");
  Serial.println("========================================");
  Serial.println();
  Serial.println("Commands:");
  Serial.println("  SERVO <0-180>  : Move servo to specified angle");
  Serial.println("  SERVO_SWEEP    : Run full diagnostic sweep");
  Serial.println("  JSON format    : {\"cmd\":\"servo\",\"angle\":90}");
  Serial.println();
}

void loop() {
  // Read Serial input
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        handleSerialCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
      // Prevent buffer overflow
      if (serialBuffer.length() > 512) {
        serialBuffer = "";
      }
    }
  }

  // Timeout: return to SAFE if no alert received recently
  if (currentZone != "SAFE" && (millis() - lastAlertTime > ALERT_TIMEOUT_MS)) {
    Serial.println("[Alert] Timeout - returning to SAFE zone");
    setZoneSafe();
  }

  // Drive buzzer based on current alert state
  updateBuzzer();

  // Real-time ultrasonic telemetry (100ms interval = 10 Hz)
  static unsigned long lastDistRead = 0;
  if (millis() - lastDistRead >= 100) {
    lastDistRead = millis();
    long distance = readUltrasonicDistance();
    if (distance > 0 && distance < 400) {
      Serial.print("{\"telemetry\":\"distance\",\"distance_cm\":");
      Serial.print(distance);
      Serial.println("}");
    }
    // CRITICAL SAFETY RULE:
    // HC-SR04 proximity ALONE does NOT activate the human danger buzzer.
    // The buzzer activates strictly based on camera-based human detection
    // fused with HC-SR04 proximity commands from SafeSight AI.
  }

  // Serial heartbeat
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    lastHeartbeat = millis();
    long dist = readUltrasonicDistance();
    Serial.print("{\"status\":\"heartbeat\",\"zone\":\"");
    Serial.print(currentZone);
    Serial.print("\",\"distance_cm\":");
    Serial.print(dist);
    Serial.print(",\"uptime_ms\":");
    Serial.print(millis());
    Serial.println("}");
  }
}

// ========================
// Serial Command Handler
// ========================
void handleSerialCommand(String input) {
  input.trim();

  // Handle simple single-char commands for backward compatibility
  if (input == "S") {
    // Legacy start/alert command
    Serial.println("[Legacy] Received 'S' - activating buzzer");
    currentZone = "DANGER";
    vibrationMode = "pulsed";
    soundMode = "off";
    lastAlertTime = millis();
    return;
  }
  if (input == "R") {
    // Legacy reset/stop command
    Serial.println("[Legacy] Received 'R' - deactivating buzzer");
    setZoneSafe();
    return;
  }

  // Diagnostic commands
  if (input.startsWith("SERVO ")) {
    int angle = input.substring(6).toInt();
    setServoAngle(angle);
    return;
  }
  if (input == "SERVO" || input == "SERVO_SWEEP" || input == "MOTOR") {
    testServoDiagnostics();
    return;
  }
  if (input == "PING" || input == "HCSR04") {
    testUltrasonicDiagnostics();
    return;
  }
  if (input == "SCAN_PINS") {
    scanUltrasonicPins();
    return;
  }
  if (input == "CHECK_ALL") {
    Serial.println("{\"status\":\"check_all_start\"}");
    testUltrasonicDiagnostics();
    testServoDiagnostics();
    Serial.println("{\"status\":\"check_all_done\"}");
    return;
  }

  // Handle JSON commands from SafeSight AI pipeline
  if (input.startsWith("{")) {
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, input);

    if (error) {
      Serial.print("[JSON] Parse error: ");
      Serial.println(error.c_str());
      return;
    }

    // Check for diagnostic commands in JSON
    if (doc["cmd"].is<const char*>()) {
      String cmd = doc["cmd"].as<String>();
      if (cmd == "ping" || cmd == "hcsr04") {
        testUltrasonicDiagnostics();
        return;
      }
      if (cmd == "servo") {
        int angle = doc["angle"] | 90;
        setServoAngle(angle);
        return;
      }
      if (cmd == "sweep" || cmd == "servo_sweep" || cmd == "motor") {
        testServoDiagnostics();
        return;
      }
      if (cmd == "check_all") {
        testUltrasonicDiagnostics();
        testServoDiagnostics();
        return;
      }
    }

    // Direct servo angle in JSON
    if (doc["servo"].is<int>()) {
      setServoAngle(doc["servo"].as<int>());
    }

    // Extract fields (matching communication.py payload)
    const char* zone = doc["zone"] | "SAFE";
    const char* vibration = doc["vibration"] | "off";
    const char* light = doc["light"] | "off";
    const char* sound = doc["sound"] | "off";
    int workerId = doc["worker_id"] | -1;

    // Update state
    currentZone = String(zone);
    vibrationMode = String(vibration);
    soundMode = String(sound);
    lastAlertTime = millis();

    // Reset single pulse tracking for new alerts
    singlePulseActive = false;

    // Acknowledge
    Serial.print("{\"ack\":true,\"zone\":\"");
    Serial.print(currentZone);
    Serial.print("\",\"servo_angle\":");
    Serial.print(currentServoAngle);
    Serial.print(",\"worker_id\":");
    Serial.print(workerId);
    Serial.println("}");

    // Servo position & alarm feedback based on safety zone
    if (currentZone == "CRITICAL") {
      setServoAngle(90);  // 90° deployed critical safety barrier
    } else if (currentZone == "WARNING") {
      setServoAngle(45);  // 45° warning caution position
    } else if (currentZone == "SAFE") {
      setZoneSafe();
    }

    return;
  }

  // Unknown command
  Serial.print("[CMD] Unknown: ");
  Serial.println(input);
}

// ========================
// Zone Reset
// ========================
void setZoneSafe() {
  currentZone = "SAFE";
  vibrationMode = "off";
  soundMode = "off";
  digitalWrite(BUZZER_PIN, LOW);
  buzzerState = false;
  singlePulseActive = false;
  setServoAngle(0); // Return servo to safe 0° position
}

// ========================
// Buzzer Control
// ========================
void updateBuzzer() {
  unsigned long now = millis();

  if (vibrationMode == "off" && soundMode == "off") {
    digitalWrite(BUZZER_PIN, LOW);
    buzzerState = false;
    singlePulseActive = false;
    return;
  }

  // ---- WARNING: single_pulse ----
  if (vibrationMode == "single_pulse") {
    if (!singlePulseActive) {
      singlePulseActive = true;
      singlePulseStart = now;
      digitalWrite(BUZZER_PIN, HIGH);
      buzzerState = true;
    } else if (now - singlePulseStart >= SINGLE_PULSE_DURATION) {
      digitalWrite(BUZZER_PIN, LOW);
      buzzerState = false;
    }
    return;
  }

  // ---- DANGER: pulsed (rapid on/off) ----
  if (vibrationMode == "pulsed") {
    singlePulseActive = false;
    const unsigned long PULSE_INTERVAL = 150; // ms
    if (now - lastBuzzerToggle >= PULSE_INTERVAL) {
      lastBuzzerToggle = now;
      buzzerState = !buzzerState;
      digitalWrite(BUZZER_PIN, buzzerState ? HIGH : LOW);
    }
    return;
  }

  // ---- CRITICAL: continuous_high ----
  if (vibrationMode == "continuous_high" || soundMode == "on") {
    singlePulseActive = false;
    if (!buzzerState) {
      digitalWrite(BUZZER_PIN, HIGH);
      buzzerState = true;
    }
    return;
  }
}

// ========================
// Ultrasonic Sensor & Diagnostics
// ========================
float measureDistanceOnPins(int trigPin, int echoPin, long &durationOut, int &initialEchoState) {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  initialEchoState = digitalRead(echoPin);

  digitalWrite(trigPin, LOW);
  delayMicroseconds(4);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(12);
  digitalWrite(trigPin, LOW);

  // 40ms timeout corresponds to ~6.8 meters
  long duration = pulseIn(echoPin, HIGH, 40000);
  durationOut = duration;

  if (duration == 0) return -1.0;
  return (duration / 2.0) / 29.1;
}

void testUltrasonicDiagnostics() {
  long dur = 0;
  int initEcho = -1;
  float dist = measureDistanceOnPins(ULTRASONIC_TRIG, ULTRASONIC_ECHO, dur, initEcho);

  Serial.print("{\"component\":\"hcsr04\",\"trig\":");
  Serial.print(ULTRASONIC_TRIG);
  Serial.print(",\"echo\":");
  Serial.print(ULTRASONIC_ECHO);
  Serial.print(",\"initial_echo\":");
  Serial.print(initEcho);
  Serial.print(",\"pulse_us\":");
  Serial.print(dur);
  Serial.print(",\"dist_cm\":");
  Serial.print(dist, 1);

  if (dist > 0) {
    Serial.println(",\"status\":\"OK\"}");
    return;
  }

  // If failed on configured pins, check if TRIG and ECHO are swapped
  long durRev = 0;
  int initEchoRev = -1;
  float distRev = measureDistanceOnPins(ULTRASONIC_ECHO, ULTRASONIC_TRIG, durRev, initEchoRev);
  if (distRev > 0) {
    Serial.print(",\"status\":\"PINS_SWAPPED\",\"suggested_trig\":");
    Serial.print(ULTRASONIC_ECHO);
    Serial.print(",\"suggested_echo\":");
    Serial.print(ULTRASONIC_TRIG);
    Serial.print(",\"dist_cm\":");
    Serial.print(distRev, 1);
    Serial.println("}");
    // Restore configured pinModes
    pinMode(ULTRASONIC_TRIG, OUTPUT);
    pinMode(ULTRASONIC_ECHO, INPUT);
    return;
  }

  // Restore configured pinModes
  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);

  Serial.println(",\"status\":\"NO_ECHO\"}");
}

void scanUltrasonicPins() {
  const int pairs[][2] = {
    {25, 26}, {26, 25},
    {5, 18}, {18, 5},
    {23, 22}, {22, 23},
    {19, 21}, {21, 19},
    {4, 2}, {13, 12}, {14, 27}
  };
  int numPairs = sizeof(pairs) / sizeof(pairs[0]);
  bool found = false;

  Serial.println("{\"status\":\"pin_scan_start\"}");
  for (int i = 0; i < numPairs; i++) {
    int t = pairs[i][0];
    int e = pairs[i][1];
    long dur = 0;
    int initEcho = 0;
    float dist = measureDistanceOnPins(t, e, dur, initEcho);
    if (dist > 0 && dist < 500) {
      Serial.print("{\"scan\":\"FOUND\",\"trig\":");
      Serial.print(t);
      Serial.print(",\"echo\":");
      Serial.print(e);
      Serial.print(",\"dist_cm\":");
      Serial.print(dist, 1);
      Serial.println("}");
      found = true;
      break;
    }
  }
  // Restore configured pins
  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);

  if (!found) {
    Serial.println("{\"scan\":\"NOT_FOUND\",\"msg\":\"No ultrasonic echo on scanned pin pairs\"}");
  }
}

long readUltrasonicDistance() {
  long dur = 0;
  int initEcho = 0;
  float dist = measureDistanceOnPins(ULTRASONIC_TRIG, ULTRASONIC_ECHO, dur, initEcho);
  return (long)dist;
}

// ========================
// SG90 Servo Control & Diagnostics (GPIO 33)
// ========================
void setServoAngle(int angle) {
  angle = constrain(angle, 0, 180);
  currentServoAngle = angle;
  sg90Servo.write(angle);
  Serial.print("{\"component\":\"servo\",\"pin\":33,\"angle\":");
  Serial.print(angle);
  Serial.println(",\"status\":\"OK\"}");
}

void activateMotorVibration() {
  setServoAngle(90);
}

void stopMotor() {
  setServoAngle(0);
}

void testServoDiagnostics() {
  Serial.println("{\"component\":\"servo\",\"step\":\"diagnostic_start\"}");
  int testAngles[] = {0, 45, 90, 135, 180, 90, 0};
  for (int i = 0; i < 7; i++) {
    int ang = testAngles[i];
    setServoAngle(ang);
    delay(500);
  }
  Serial.println("{\"component\":\"servo\",\"step\":\"diagnostic_done\"}");
}

void testMotorDiagnostics() {
  testServoDiagnostics();
}