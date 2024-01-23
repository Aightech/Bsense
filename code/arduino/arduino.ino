#define PIN_TRIG 3
#define PIN_VIB_11 11
#define PIN_VIB_12 12
#define PIN_BUZZER_TONE 6
#define PIN_BUZZER_AMP 8
#define FREQ_BUZZ 1000  //defined frequence for the buzzer

int buzz_amp[3] = { 0, 1, 2 };
int vib1_amp[3] = { 0, 1, 2 };
int vib2_amp[3] = { 0, 1, 2 };
int vibr_amp[3] = { 0, 1, 2 };

uint8_t ampVib1 = 0;
uint8_t ampVib2 = 0;
uint8_t ampBuzz = 0;
uint8_t period = 0;

int delay_ms_vib1 = 0;
int delay_ms_vib2 = 0;
int delay_ms_buzz = 0;



void blockingAnalogWrite(uint8_t pin, double alpha, double dt, int freq = 20000) {
  int delay1 = 1000000. / freq;
  int delay2 = delay1 * (1 - alpha);
  delay1 *= alpha;
  int len = dt * freq;
  for (int i = 0; i < len; i++) {
    digitalWrite(PIN_VIB_11, HIGH);  // turn the LED on (HIGH is the voltage level)
    delayMicroseconds(delay1);       // wait for a second
    digitalWrite(PIN_VIB_11, LOW);   // turn the LED off by making the voltage LOW
    delayMicroseconds(delay2);       // wait for a second
  }
}

void smoothDown(double fromAlpha, double dt) {
  double inc = -(fromAlpha - 0.5) / 50.;
  int sign = inc / abs(inc);
  for (double alpha = fromAlpha; alpha > 0.5; alpha += inc)
    blockingAnalogWrite(PIN_VIB_11, alpha, dt / 50.);
}

void setup() {
  // Initialize pins
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_VIB_11, OUTPUT);
  pinMode(PIN_VIB_12, OUTPUT);
  pinMode(PIN_BUZZER_TONE, OUTPUT);
  pinMode(PIN_BUZZER_AMP, OUTPUT);

  digitalWrite(PIN_VIB_11, LOW);
  digitalWrite(PIN_VIB_12, LOW);

  // Initialize Serial communication and button pin
  Serial.begin(9600);
  delay(100);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {

  if (Serial.available() >= 4) 
  {
    ampVib1 = Serial.read();
    ampVib2 = Serial.read();
    ampBuzz = Serial.read();
    period = Serial.read();

    analogWrite(PIN_BUZZER_AMP, ampBuzz);
    digitalWrite(LED_BUILTIN, HIGH);
    tone(PIN_BUZZER_TONE, FREQ_BUZZ);

    if (ampVib1) {
      double alpha = 0.8+ampVib1/1280.;
      blockingAnalogWrite(PIN_VIB_11, alpha, 0.1);
      smoothDown(alpha, 0.1);

      digitalWrite(PIN_VIB_11, LOW);
      delay(max(0,period*10.-200));
    }
    else
      delay(period*10);

    
    noTone(PIN_BUZZER_TONE);
    // Blink the built-in LED to indicate loop execution
    Serial.write(ampVib1 + ampVib2 + ampBuzz + period);
  }
  delay(1);
  digitalWrite(LED_BUILTIN, LOW);
}