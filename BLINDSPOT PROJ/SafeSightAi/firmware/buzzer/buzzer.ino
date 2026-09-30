#include <Arduino.h>

#define TRIG_PIN 23  // GPIO Pin for Trigger
#define ECHO_PIN 22  // GPIO Pin for Echo
#define BUZZER_PIN 21 // GPIO Pin for Buzzer

// Constants
const int THRESHOLD = 20; // Threshold distance in cm (for buzzer activation)

void setup() {
  // Start serial communication for debugging
  Serial.begin(115200);
  
  // Set up pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Ensure buzzer is off initially
  digitalWrite(BUZZER_PIN, LOW);
}

void loop() {
  // Trigger pulse to the Ultrasonic Sensor
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Read the duration of the Echo pulse (30000 microseconds timeout = ~5 meters)
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  
  if (duration == 0) {
    Serial.println("Warning: No echo received (Sensor disconnected or out of range)");
    digitalWrite(BUZZER_PIN, LOW);  // Keep buzzer off on timeout/error
  } else {
    // Calculate distance in cm
    long distance = (duration / 2) / 29.1; // Speed of sound = 343 m/s = 29.1 microseconds per cm
    
    // Output the distance for debugging
    Serial.print("Distance: ");
    Serial.print(distance);
    Serial.println(" cm");
    
    // If the distance is below the threshold, activate the buzzer
    if (distance > 0 && distance < THRESHOLD) {
      digitalWrite(BUZZER_PIN, HIGH);  // Turn on buzzer
    } else {
      digitalWrite(BUZZER_PIN, LOW);   // Turn off buzzer
    }
  }
  
  // Wait a little before taking the next measurement
  delay(500);
}