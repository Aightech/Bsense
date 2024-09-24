#define TIMER_INTERRUPT_DEBUG         2
#define _TIMERINTERRUPT_LOGLEVEL_     0
#define USE_TIMER_3     true
#warning Using Timer3

#include "TimerInterrupt.h"


#define TIMER_INTERVAL_MS        1
#define DEBOUNCING_INTERVAL_MS    80

#define LOCAL_DEBUG      1

volatile unsigned long rotationTime = 0;
float RPM       = 0.00;
float avgRPM    = 0.00;

volatile int debounceCounter;

#define PIN_TRIG 52
#define PIN_VIB1_A 11
#define PIN_VIB1_B 12

#define PIN_VIB2_PWM 14
#define PIN_VIB2_PH 15

#define PIN_BUZZER_TONE 6
#define PIN_BUZZER_AMP 8
#define FREQ_BUZZ 1000  //defined frequence for the buzzer

#define STARTING_CHAR 0xaa // 170 ascii code: ª

int buzz_amp[3] = { 0, 1, 2 };
int vib1_amp[3] = { 0, 1, 2 };
int vib2_amp[3] = { 0, 1, 2 };
int vibr_amp[3] = { 0, 1, 2 };

uint8_t ampVib1 = 0;
uint8_t ampVib2 = 0;
uint8_t ampBuzz = 0;
uint8_t period = 0;

unsigned long  delay_ms_vib1 = 0;

unsigned long  delay_ms_vib2 = 0;
unsigned long  delay_ms_buzz = 0;
unsigned long delay_trig = 0;
bool vib1_state = false;
bool vib2_state = false;
bool buzz_state = false;

uint8_t source;
uint8_t v1;
uint8_t v2;
uint16_t dt;

uint8_t buff[1000];
unsigned long t_us = 0;

void TimerHandler()
{
  t_us = micros();
  if(t_us<delay_ms_vib1)
  { 
    //the pulse is sill on
  }
  else if (vib1_state) // if the delay is over and the pulse is still on: turn it off
  {
    vib1(false);
  }

  if(t_us<delay_ms_vib2)
  { 
    vib2(255,false);
  }
  else if (vib2_state)
  {
    vib2(false,false);
  }

  if(t_us<delay_ms_buzz)
  { 
    //the buzzer is still on
  }
  else if (buzz_state)
  {// if te delay is over and the buzzer is still on: switch it off
    buzzer(0,0);
    buzz_state = false;
  }

  if(t_us> delay_trig)
  {
    digitalWrite(PIN_TRIG, LOW);
    digitalWrite(LED_BUILTIN, LOW);
  }
}

void vib1(bool state)
{
  digitalWrite(PIN_VIB1_A,state);
  vib1_state = state;
}

void vib2(int amp, bool dir)
{
  analogWrite(PIN_VIB2_PWM,amp);
  digitalWrite(PIN_VIB2_PH,dir);
  vib2_state = amp;
}


void buzzer(int amp, int tone)
{
  analogWrite(PIN_BUZZER_AMP, amp);
  analogWrite(PIN_BUZZER_TONE, tone);
  buzz_state = amp;
}



void setup() {
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
  digitalWrite(PIN_BUZZER_AMP,HIGH);

  

  // Initialize Serial communication and button pin
  Serial.begin(115200);
  delay(100);
  pinMode(LED_BUILTIN, OUTPUT);


  ITimer3.init();
  ITimer3.attachInterruptInterval(TIMER_INTERVAL_MS, TimerHandler);
}

void loop() 
{
  if(Serial.available() >= 6)
  {
    int n = 6;
    Serial.readBytes((char*)&buff, n);
    int i = 0;
    while (i<n)
    {
      if (buff[i] == STARTING_CHAR)
      {
        source = buff[i+1];// read what type of stimulus is {v: vibration1, w: vibration2, b: buzzer}
        v1 = buff[i+2]; // read the first parameter of the stimulus
        v2 = buff[i+3]; // read the second parameter of the stimulus
        dt = buff[i+4] + buff[i+5]*256; // read the time duration of the stimulus (used only for the buzzer)
        digitalWrite(PIN_TRIG, HIGH);// set the trigger pin high
        digitalWrite(LED_BUILTIN, HIGH); // turn on the led (while the trigger is high)
        delay_trig = micros() + 5000;//the trigger pulse is 5ms
        switch (source)
        {
          case 'v': // trigger a pulse for the vibration1
            vib1(v1);
            delay_ms_vib1 = micros() + 100;//*dt; //the vibration1 pulse is 100us
            break;
          case 'w': // trigger a pulse for the vibration2
            vib2(v1,v2);
            delay_ms_vib2 = micros() + 100;//*dt; //the vibration2 pulse is 100us
            break;
          case 'b': // trigger a pulse for the buzzer
            buzzer(v1,v2);
            delay_ms_buzz = micros() + 100*dt; //the buzzer pulse is 100us*duration
            break;
          default:  
            break;
        }
        i = n;
      }
      i++;
    }
    buff[0] = n;
    // Serial.write((char*)&buff, n);
  }

    

}