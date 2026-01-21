#define TIMER_INTERRUPT_DEBUG 2
#define _TIMERINTERRUPT_LOGLEVEL_ 0
#define USE_TIMER_3 true
#warning Using Timer3

#include "TimerInterrupt.h"

#define TIMER_INTERVAL_MS 1

#define PIN_TRIG 52
#define PIN_VIB1_A 11
#define PIN_VIB1_B 12

#define PIN_VIB2_PWM 14
#define PIN_VIB2_PH 15

#define PIN_BUZZER_TONE 6
#define PIN_BUZZER_AMP 8

#define STARTING_CHAR 0xaa // 170 ascii code: ª

uint8_t ampVib1 = 0;
uint16_t freqVib1 = 0;
uint8_t ampVib2 = 0;
uint16_t freqVib2 = 0;
uint8_t ampBuzz = 0;
uint16_t toneBuzz = 0;
uint16_t timeBuzz = 0;

unsigned long micros_time = 0;
unsigned long start_us_vib1 = 0;
unsigned long duration_us_vib1 = 0;
unsigned long start_us_vib2 = 0;
unsigned long duration_us_vib2 = 0;
unsigned long start_us_buzz = 0;
unsigned long duration_us_buzz = 0;
unsigned long start_us_trig = 0;
unsigned long duration_us_trig = 5000;  // 5ms trigger pulse
bool vib1_state = false;
bool vib2_state = false;
bool buzz_state = false;
bool trig_state = false;

uint8_t source;
uint8_t len;

uint8_t buff[64];
unsigned long t_us = 0;

void TimerHandler()
{
  t_us = micros();

  // Use elapsed time comparisons to handle micros() overflow correctly
  if (vib1_state && (t_us - start_us_vib1) >= duration_us_vib1)
  {
    vib1(false);
  }

  if (vib2_state && (t_us - start_us_vib2) >= duration_us_vib2)
  {
    vib2(false);
  }

  if (buzz_state && (t_us - start_us_buzz) >= duration_us_buzz)
  {
    buzzer(0, 0);
    buzz_state = false;
  }

  if (trig_state && (t_us - start_us_trig) >= duration_us_trig)
  {
    trigger_pulse(false);
  }
}

void vib1(bool state) // switch the vibration1 on or off
{
  digitalWrite(PIN_VIB1_A, state);
  vib1_state = state;
}

void vib2(int amp) // set the vibration2 amplitude and direction
{
  analogWrite(PIN_VIB2_PWM, amp);
  digitalWrite(PIN_VIB2_PH, false);
  vib2_state = amp;
}

void buzzer(int amp, uint16_t freq) // set the buzzer amplitude and frequency
{
  analogWrite(PIN_BUZZER_AMP, amp);
  if (freq > 0 && amp > 0)
  {
    tone(PIN_BUZZER_TONE, freq);
  }
  else
  {
    noTone(PIN_BUZZER_TONE);
  }
  buzz_state = amp;
}

void trigger_pulse(bool state) // trigger a pulse on the trigger pin
{
  digitalWrite(PIN_TRIG, state);
  digitalWrite(LED_BUILTIN, state);
  trig_state = state;
}

void setup()
{
  // Initialize pins
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_VIB1_A, OUTPUT);
  pinMode(PIN_VIB1_B, OUTPUT);
  digitalWrite(PIN_VIB1_A, LOW);
  digitalWrite(PIN_VIB1_B, LOW);

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

  ITimer3.init();
  ITimer3.attachInterruptInterval(TIMER_INTERVAL_MS, TimerHandler);
}

void loop()
{
  if (Serial.available() >= 3)
  {
    Serial.readBytes((char *)&buff, 3);
    if (buff[0] == STARTING_CHAR)
    {
      source = buff[1];                // read what type of stimulus is {v: vibration1, w: vibration2, b: buzzer}
      len = buff[2];                   // read the length of the message
      if (len > sizeof(buff))          // bounds check to prevent buffer overflow
      {
        while (Serial.available()) Serial.read(); // flush invalid data
        return;
      }
      // Wait for remaining data with timeout (non-blocking check)
      unsigned long wait_start = millis();
      while (Serial.available() < len && (millis() - wait_start) < 100) {
        // Brief yield, timeout after 100ms
      }
      if (Serial.available() < len) {
        return; // Timeout - incomplete message, skip
      }
      Serial.readBytes((char *)&buff, len); // read the message

      // Validate message length for each command type
      uint8_t expected_len = 0;
      if (source == 'v' || source == 'w' || source == 'b') expected_len = 5;
      else if (source == 'c') expected_len = 10;
      if (expected_len > 0 && len < expected_len) {
        return; // Invalid message length
      }

      micros_time = micros();          // get the current time
      trigger_pulse(true);             // trigger a pulse on the trigger pin
      start_us_trig = micros_time;     // record start time for trigger
      switch (source)
      {
      case 'v': // trigger a pulse for the vibration1
        ampVib1 = buff[0]; // read the amplitude of the vibration1
        freqVib1 = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
        vib1(ampVib1);
        start_us_vib1 = micros_time;
        duration_us_vib1 = 100; // the vibration1 pulse is 100us
        break;
      case 'w': // trigger a pulse for the vibration2
        ampVib2 = buff[0]; // read the amplitude of the vibration2
        freqVib2 = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
        vib2(ampVib2);
        start_us_vib2 = micros_time;
        duration_us_vib2 = 100; // the vibration2 pulse is 100us
        break;
      case 'b': // trigger a pulse for the buzzer
        ampBuzz = buff[0]; // read the amplitude of the buzzer
        toneBuzz = *((uint16_t *)&buff[1]); // read the tone of the buzzer (2 bytes)
        timeBuzz = *((uint16_t *)&buff[3]); // read the duration of the buzzer (ms)
        buzzer(ampBuzz, toneBuzz);
        start_us_buzz = micros_time;
        duration_us_buzz = (unsigned long)timeBuzz * 1000; // convert ms to us
        break;
      case 'c':// combination of Buzzer and Vibration1
        ampVib1 = buff[0]; // read the amplitude of the vibration1
        freqVib1 = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
        // duration at buff[3-4]
        ampBuzz = buff[5]; // read the amplitude of the buzzer
        toneBuzz = *((uint16_t *)&buff[6]); // read the tone of the buzzer (2 bytes)
        timeBuzz = *((uint16_t *)&buff[8]); // read the duration of the buzzer (ms)
        vib1(ampVib1);
        start_us_vib1 = micros_time;
        duration_us_vib1 = 100; // the vibration1 pulse is 100us
        buzzer(ampBuzz, toneBuzz);
        start_us_buzz = micros_time;
        duration_us_buzz = (unsigned long)timeBuzz * 1000; // convert ms to us
        break;
      default:
        break;
      }
    }
  }
}