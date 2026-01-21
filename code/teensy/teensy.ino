#define TIMER_INTERVAL_US 1000

#define PIN_TRIG 2
#define PIN_VIB1_PWM 0
#define PIN_VIB1_PH 1

#define PIN_VIB2_PWM 2
#define PIN_VIB2_PH 3

#define PIN_BUZZER_TONE 4
#define PIN_BUZZER_AMP 3

#define STARTING_CHAR 0xaa

IntervalTimer myTimer;

uint8_t ampVib1 = 0;
uint32_t periodVib1 = 0;
uint8_t ampVib2 = 0;
uint32_t periodVib2 = 0;
uint8_t ampBuzz = 0;
uint32_t periodBuzz = 0;
uint16_t timeBuzz = 0;

unsigned long micros_time = 0;
unsigned long start_us_vib1 = 0;
unsigned long end_us_vib1 = 0;
unsigned long start_us_vib2 = 0;
unsigned long end_us_vib2 = 0;
unsigned long start_us_buzz = 0;
unsigned long end_us_buzz = 0;
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

    if (vib1_state)
    {
        if (t_us >= end_us_vib1)
        { // if the duration is over: turn it off
            vib1(0, LOW);
            vib1_state = false;
        }
        else if (periodVib1 > 0)
        {
            // Calculate direction based on elapsed time from start
            unsigned long elapsed = t_us - start_us_vib1;
            unsigned long half_period = periodVib1 / 2;
            bool dir = (half_period > 0) ? ((elapsed / half_period) % 2) : LOW;
            vib1(ampVib1, dir);
        }
    }

    if (vib2_state && t_us >= end_us_vib2)
    { // if the duration is over: turn it off
        vib2(false);
        vib2_state = false;
    }

    if (buzz_state)
    {
        if (t_us >= end_us_buzz)
        { // if the duration is over: turn it off
            buzzer(0, LOW);
            buzz_state = false;
        }
        else if (periodBuzz > 0)
        {
            // Calculate direction based on elapsed time from start
            unsigned long elapsed = t_us - start_us_buzz;
            unsigned long half_period = periodBuzz / 2;
            bool dir = (half_period > 0) ? ((elapsed / half_period) % 2) : LOW;
            buzzer(ampBuzz, dir);
        }
    }

    if (t_us >= delay_trig)
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
    analogWriteResolution(9);
    // Initialize pins
    pinMode(PIN_TRIG, OUTPUT);
    pinMode(PIN_VIB1_PWM, OUTPUT);
    analogWriteFrequency(PIN_VIB1_PWM, 46875);
    pinMode(PIN_VIB1_PH, OUTPUT);

    pinMode(PIN_VIB2_PWM, OUTPUT);
    analogWriteFrequency(PIN_VIB2_PWM, 46875);
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
            if (len > sizeof(buff))               // bounds check to prevent buffer overflow
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

            micros_time = micros();               // get the current time
            trigger_pulse(true);                  // trigger a pulse on the trigger pin
            delay_trig = micros_time + 5000;      // the trigger pulse is 5ms
            switch (source)
            {
            case 'v':                                       // trigger a pulse for the vibration1
            {
                ampVib1 = buff[0];                          // read the amplitude of the vibration1
                uint16_t freqVib1 = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
                periodVib1 = (freqVib1 > 0) ? (1000000 / freqVib1) : 0; // calculate the period in microseconds
                start_us_vib1 = micros_time;
                end_us_vib1 = micros_time + *((uint16_t *)&buff[3]) * ((unsigned long)1000);
                vib1_state = true;
                break;
            }
            case 'w':                                       // trigger a pulse for the vibration2
            {
                ampVib2 = buff[0];                          // read the amplitude of the vibration2
                uint16_t freqVib2 = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
                periodVib2 = (freqVib2 > 0) ? (1000000 / freqVib2) : 0; // calculate the period in microseconds
                start_us_vib2 = micros_time;
                end_us_vib2 = micros_time + *((uint16_t *)&buff[3]) * ((unsigned long)1000);
                vib2_state = true;
                break;
            }
            case 'b':                                       // trigger a pulse for the buzzer
            {
                ampBuzz = buff[0];                          // read the amplitude of the buzzer
                uint16_t freqBuzz = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
                periodBuzz = (freqBuzz > 0) ? (1000000 / freqBuzz) : 0; // calculate the period in microseconds
                start_us_buzz = micros_time;
                end_us_buzz = micros_time + *((uint16_t *)&buff[3]) * ((unsigned long)1000);
                buzz_state = true;
                break;
            }
            case 'c':                                       // combination of Buzzer and Vibration1
            {
                ampVib1 = buff[0];                          // read the amplitude of the vibration1
                uint16_t freqVib1 = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
                periodVib1 = (freqVib1 > 0) ? (1000000 / freqVib1) : 0; // calculate the period in microseconds
                start_us_vib1 = micros_time;
                end_us_vib1 = micros_time + *((uint16_t *)&buff[3]) * ((unsigned long)1000);
                ampBuzz = buff[5];                          // read the amplitude of the buzzer
                uint16_t freqBuzz = *((uint16_t *)&buff[6]); // read the frequency (2 bytes)
                periodBuzz = (freqBuzz > 0) ? (1000000 / freqBuzz) : 0; // calculate the period in microseconds
                start_us_buzz = micros_time;
                end_us_buzz = micros_time + *((uint16_t *)&buff[8]) * ((unsigned long)1000);
                vib1_state = true;
                buzz_state = true;
                break;
            }
            default:
                break;
            }
        }
    }
}