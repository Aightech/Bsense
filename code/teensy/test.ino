// // #include <Arduino.h>
// #define PWM_PIN 0
// #define DIR_PIN 1


// void setup() {
//   // Initialize serial communication
//   Serial.begin(9600);
  
//   // Set pin modes
//   pinMode(PWM_PIN, OUTPUT); // Set PWM pin as output
//   pinMode(DIR_PIN, OUTPUT); // Set direction pin as output
//   digitalWrite(DIR_PIN, HIGH); // Set direction to HIGH
//   //set pwm frequency
//   analogWriteFrequency(PWM_PIN, 60000); // Set PWM frequency to 1
//   analogWriteResolution(10); // Set PWM resolution to 10 bits
// }

// // void loop() {
// //   // Blink the built-in LED
// //   analogWrite(PWM_PIN, 1000); // Turn the LED on
// //   delay(50);                      // Wait for a second
// //   analogWrite(PWM_PIN, 0);  // Turn the LED off
// //   delay(3000);                      // Wait for a second
// // }

// void loop() {
//   // Blink the built-in LED
//   int t=0;
//   int dt = 1000/ 60; // Set the delay time in milliseconds (1000 ms / 60 = 16.67 ms)
//   analogWrite(PWM_PIN, 100); // Turn the LED on
//   while(t<dt){
//     digitalWrite(DIR_PIN, HIGH); // Set direction to HIGH
//     delay(dt/2);// Wait for a second
//     digitalWrite(DIR_PIN, LOW); // Set direction to LOW
//     delay(dt/2);                      // Wait for a second
//     t+=dt;
//   }
//   analogWrite(PWM_PIN, 0);
//   delay(3000);    
// }