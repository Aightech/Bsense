#include <Arduino.h>
#line 1 "/home/adev/dev/bsense/code/teensy/teensy.ino"
// #include <Arduino.h>
#define PWM_PIN 12
#define DIR_PIN 11


#line 6 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void setup();
#line 16 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void loop();
#line 6 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Set pin modes
  pinMode(PWM_PIN, OUTPUT); // Set PWM pin as output
  pinMode(DIR_PIN, OUTPUT); // Set direction pin as output
  digitalWrite(DIR_PIN, HIGH); // Set direction to HIGH
}

void loop() {
  // Blink the built-in LED
  digitalWrite(DIR_PIN, HIGH); // Turn the LED on
  delay(500);                      // Wait for a second
  digitalWrite(DIR_PIN, LOW);  // Turn the LED off
  delay(500);                      // Wait for a second
}
