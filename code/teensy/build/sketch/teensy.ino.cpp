#include <Arduino.h>
#line 1 "/home/adev/dev/bsense/code/teensy/teensy.ino"
#define TIMER_INTERVAL_US 1000

#define PIN_TRIG 12
#define PIN_VIB1_PWM 0
#define PIN_VIB1_PH 1

#define PIN_VIB2_PWM 2
#define PIN_VIB2_PH 3

#define PIN_BUZZER_TONE 4
#define PIN_BUZZER_AMP 3

#define STARTING_CHAR 0xaa

IntervalTimer myTimer;

uint8_t ampVib1 = 0;
uint64_t periodVib1 = 0;
uint8_t ampVib2 = 0;
uint8_t ampBuzz = 0;
uint8_t periodBuzz = 0;
uint16_t timeBuzz = 0;

unsigned long micros_time = 0;
unsigned long delay_us_vib1 = 0;
unsigned long delay_us_vib2 = 0;
unsigned long delay_us_buzz = 0;
unsigned long delay_trig = 0;
bool vib1_state = false;
bool vib2_state = false;
bool buzz_state = false;

uint8_t source;
uint8_t len;

uint8_t buff[64];
unsigned long t_us = 0;

#line 39 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void TimerHandler();
#line 83 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void vib1(int amp, bool dir);
#line 89 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void vib2(int amp);
#line 96 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void buzzer(int amp, bool dir);
#line 103 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void trigger_pulse(bool state);
#line 109 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void setup();
#line 132 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void loop();
#line 39 "/home/adev/dev/bsense/code/teensy/teensy.ino"
void TimerHandler()
{
    t_us = micros();
    if (vib1_state)
    {
        if (t_us > delay_us_vib1)
        { // if the delay is over and the pulse is still on: turn it off
            vib1(0, LOW);
            vib1_state = false; // update the state
        }
        else
        {
            // dir is updated based on the frequency
            bool dir = ((t_us - delay_us_vib1) / (periodVib1 / 2)) % 2; // toggle direction every half period
            vib1(ampVib1, dir);                                         // set the vibration1 amplitude and direction
        }
    }

    if (t_us > delay_us_vib2 && vib2_state)
    { // if the delay is over and the pulse is still on: turn it off
        vib2(false);
    }

    if (buzz_state)
    {
        if (t_us > delay_us_buzz)
        { // if te delay is over and the buzzer is still on: switch it off
            buzzer(0, 0);
            buzz_state = false;
        }
        else
        {
            // dir is updated based on the frequency
            bool dir = ((t_us - delay_us_buzz) / (periodBuzz / 2)) % 2; // toggle direction every half period
            buzzer(ampBuzz, dir); // set the buzzer amplitude and tone
        }
    }

    if (t_us > delay_trig)
    {
        trigger_pulse(false);
    }
}

void vib1(int amp, bool dir) // switch the vibration1 on or off
{
    analogWrite(PIN_VIB1_PWM, amp * 4);
    digitalWrite(PIN_VIB1_PH, dir);
}

void vib2(int amp) // set the vibration2 amplitude and direction
{
    analogWrite(PIN_VIB2_PWM, amp);
    digitalWrite(PIN_VIB2_PH, false);
    vib2_state = amp;
}

void buzzer(int amp, bool dir) // set the buzzer amplitude and tone
{
    analogWrite(PIN_BUZZER_AMP, amp*4);
    digitalWrite(PIN_BUZZER_TONE, dir);
    buzz_state = amp;
}

void trigger_pulse(bool state) // trigger a pulse on the trigger pin
{
    digitalWrite(PIN_TRIG, state);
    digitalWrite(LED_BUILTIN, state);
}

void setup()
{
    // Initialize pins
    pinMode(PIN_TRIG, OUTPUT);
    pinMode(PIN_VIB1_PWM, OUTPUT);
    pinMode(PIN_VIB1_PH, OUTPUT);

    pinMode(PIN_VIB2_PWM, OUTPUT);
    pinMode(PIN_VIB2_PH, OUTPUT);

    pinMode(PIN_BUZZER_TONE, OUTPUT);
    pinMode(PIN_BUZZER_AMP, OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(PIN_BUZZER_AMP, HIGH);

    // Initialize Serial communication and button pin
    Serial.begin(115200);
    delay(100);
    pinMode(LED_BUILTIN, OUTPUT);

    myTimer.begin(TimerHandler, TIMER_INTERVAL_US); // start the timer with the handler and interval
}

void loop()
{
    if (Serial.available() >= 3)
    {
        Serial.readBytes((char *)&buff, 3);
        if (buff[0] == STARTING_CHAR)
        {
            source = buff[1];                     // read what type of stimulus is {v: vibration1, w: vibration2, b: buzzer}
            len = buff[2];                        // read the length of the message
            Serial.readBytes((char *)&buff, len); // read the message
            micros_time = micros();               // get the current time
            trigger_pulse(true);                  // trigger a pulse on the trigger pin
            delay_trig = micros_time + 5000;      // the trigger pulse is 5ms
            switch (source)
            {
            case 'v':                                       // trigger a pulse for the vibration1
                ampVib1 = buff[0];                          // read the amplitude of the vibration1
                periodVib1 = 1000000 / ((uint32_t)buff[1]); // calculate the period of the vibration1 in microseconds
                delay_us_vib1 = micros_time + *((uint16_t *)&buff[2]) * ((unsigned long)1000);
                vib1_state = true; // update the state
                break;
            case 'w':                                                                          // trigger a pulse for the vibration2
                ampVib2 = buff[0];                                                             // read the amplitude of the vibration2
                periodVib1 = 1000000 / ((uint32_t)buff[1]);                                    // calculate the period of the vibration2 in microseconds
                delay_us_vib2 = micros_time + *((uint16_t *)&buff[2]) * ((unsigned long)1000); // the vibration2 pulse is 1000us*duration
                vib2_state = true;                                                             // update the state
                break;
            case 'b':                               // trigger a pulse for the buzzer
                ampBuzz = buff[0];                  // read the amplitude of the buzzer
                periodBuzz = 1000000 / ((uint32_t)buff[1]); // calculate the period of the buzzer in microseconds
                delay_us_buzz = micros_time + *((uint16_t *)&buff[2]) * ((unsigned long)1000); // the buzzer pulse is 1000us*duration
                buzz_state = true; // update the state
                break;
            case 'c':                               // combination of Buzzer and Vibration1
                ampVib1 = buff[0];                  // read the amplitude of the vibration1
                periodVib1 = 1000000 / ((uint32_t)buff[1]); // calculate the period of the vibration1 in microseconds
                delay_us_vib1 = micros_time + *((uint16_t *)&buff[2]) * ((unsigned long)1000); // the vibration1 pulse is 1000us*duration
                ampBuzz = buff[4];                  // read the amplitude of the buzzer
                periodBuzz = 1000000 / ((uint32_t)buff[5]); // calculate the period of the buzzer in microseconds
                delay_us_buzz = micros_time + *((uint16_t *)&buff[6]) * ((unsigned long)1000); // the buzzer pulse is 1000us*duration
                vib1_state = true;                  // update the state
                buzz_state = true;                  // update the state
                break;
            default:
                break;
            }
        }
    }
}
#line 1 "/home/adev/dev/bsense/code/teensy/test.ino"
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
