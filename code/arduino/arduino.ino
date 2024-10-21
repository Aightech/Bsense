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
uint8_t ampVib2 = 0;
uint8_t ampBuzz = 0;
uint8_t toneBuzz = 0;
uint16_t timeBuzz = 0;

unsigned long micros_time = 0;
unsigned long delay_ms_vib1 = 0;
unsigned long delay_ms_vib2 = 0;
unsigned long delay_ms_buzz = 0;
unsigned long delay_trig = 0;
bool vib1_state = false;
bool vib2_state = false;
bool buzz_state = false;

uint8_t source;
uint8_t len;

uint8_t buff[64];
unsigned long t_us = 0;

void TimerHandler()
{
  t_us = micros();
  if (t_us > delay_ms_vib1 && vib1_state)
  { // if the delay is over and the pulse is still on: turn it off
    vib1(false);
  }

  if (t_us > delay_ms_vib2 && vib2_state)
  { // if the delay is over and the pulse is still on: turn it off
    vib2(false);
  }

  if (t_us > delay_ms_buzz && buzz_state)
  { // if te delay is over and the buzzer is still on: switch it off
    buzzer(0, 0);
    buzz_state = false;
  }

  if (t_us > delay_trig)
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

void buzzer(int amp, int tone) // set the buzzer amplitude and tone
{
  analogWrite(PIN_BUZZER_AMP, amp);
  analogWrite(PIN_BUZZER_TONE, tone);
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
      Serial.readBytes((char *)&buff, len); // read the message
      micros_time = micros();          // get the current time
      trigger_pulse(true);             // trigger a pulse on the trigger pin
      delay_trig = micros_time + 5000; // the trigger pulse is 5ms
      switch (source)
      {
      case 'v': // trigger a pulse for the vibration1
        ampVib1 = buff[0]; // read the amplitude of the vibration1
        vib1(ampVib1);
        delay_ms_vib1 = micros_time + 100; //*dt; //the vibration1 pulse is 100us
        break;
      case 'w': // trigger a pulse for the vibration2
        ampVib2 = buff[0]; // read the amplitude of the vibration2
        vib2(ampVib2);
        delay_ms_vib2 = micros_time + 100; //*dt; //the vibration2 pulse is 100us
        break;
      case 'b': // trigger a pulse for the buzzer
        ampBuzz = buff[0]; // read the amplitude of the buzzer
        toneBuzz = buff[1]; // read the tone of the buzzer
        timeBuzz = *((uint16_t *)&buff[2]); // read the duration of the buzzer
        buzzer(ampBuzz, toneBuzz);
        delay_ms_buzz = micros_time + 100 * timeBuzz; // the buzzer pulse is 100us*duration
        break;
      case 'c':// combination of Buzzer and Vibration2
        ampBuzz = buff[0]; // read the amplitude of the buzzer
        toneBuzz = buff[1]; // read the tone of the buzzer
        timeBuzz = *((uint16_t *)&buff[2]); // read the duration of the buzzer
        ampVib2 = buff[4]; // read the amplitude of the vibration2
        vib2(ampVib2);
        delay_ms_vib2 = micros_time + 100; //*dt; //the vibration2 pulse is 100us
        buzzer(ampBuzz, toneBuzz);
        delay_ms_buzz = micros_time + 100 * timeBuzz; // the buzzer pulse is 100us*duration
        break;
      default:
        break;
      }
    }
  }
}