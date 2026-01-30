/*
 * Bsense Teensy Firmware
 *
 * Controls LRA vibration motor and buzzer for haptic/audio stimuli.
 * Communicates via serial (115200 baud) with binary protocol.
 *
 * Amplitude Scaling Notes:
 * - PWM resolution: 9-bit (0-511)
 * - Teensy output: 3.3V
 * - LRA actuator rated: 1.8V
 * - Saturation occurs at ~60% duty cycle (3.3V * 0.6 = 1.98V)
 * - Amplitude 0-255 is scaled by *4 to use full PWM range
 * - Effective usable amplitude: 0-77 (values above saturate the actuator)
 *
 * Buzzer Implementation:
 * - Uses hardware PWM via analogWriteFrequency() for accurate tone generation
 * - Works well at high frequencies (e.g., 2000Hz) unlike manual toggling
 * - PIN_BUZZER_TONE: PWM frequency sets the tone (50% duty cycle)
 * - PIN_BUZZER_AMP: PWM duty cycle controls volume
 */

#define TIMER_INTERVAL_US 1000

#define PIN_TRIG 2
#define PIN_VIB1_PWM 0
#define PIN_VIB1_PH 1

// VIB2 currently unused - pins commented out to avoid conflict with PIN_TRIG
// #define PIN_VIB2_PWM 2
// #define PIN_VIB2_PH 3

#define PIN_BUZZER_TONE 4
#define PIN_BUZZER_AMP 3

#define STARTING_CHAR 0xaa

IntervalTimer myTimer;

uint8_t ampVib1 = 0;
uint32_t periodVib1 = 0;
// uint8_t ampVib2 = 0;      // VIB2 unused
// uint32_t periodVib2 = 0;  // VIB2 unused
uint8_t ampBuzz = 0;
uint16_t freqBuzz = 0;  // Buzzer frequency for analogWriteFrequency()

unsigned long micros_time = 0;
unsigned long start_us_vib1 = 0;
unsigned long end_us_vib1 = 0;
// unsigned long start_us_vib2 = 0;  // VIB2 unused
// unsigned long end_us_vib2 = 0;    // VIB2 unused
unsigned long start_us_buzz = 0;
unsigned long end_us_buzz = 0;
unsigned long delay_trig = 0;
bool vib1_state = false;
// bool vib2_state = false;  // VIB2 unused
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

    // VIB2 unused
    // if (vib2_state && t_us >= end_us_vib2)
    // {
    //     vib2(false);
    //     vib2_state = false;
    // }

    if (buzz_state && t_us >= end_us_buzz)
    {
        // Duration over - turn off buzzer
        buzzer_stop();
        buzz_state = false;
    }

    if (t_us >= delay_trig)
    {
        trigger_pulse(false);
    }
}

void vib1(int amp, bool dir) // switch the vibration1 on or off
{
    // Amplitude scaled by 4 for 9-bit PWM (0-511)
    // Note: LRA saturates at ~60% duty, so effective range is amp 0-77
    analogWrite(PIN_VIB1_PWM, amp * 2);
    digitalWrite(PIN_VIB1_PH, dir);
}

// VIB2 unused
// void vib2(int amp)
// {
//     analogWrite(PIN_VIB2_PWM, amp * 4);
//     digitalWrite(PIN_VIB2_PH, false);
//     vib2_state = (amp > 0);
// }

void buzzer_start(int amp, uint16_t freq) // start buzzer with amplitude and frequency
{
    // Use hardware PWM for tone generation (works well at high frequencies like 2000Hz)
    // Set the PWM frequency for the tone pin
    if (freq > 0) {
        analogWriteFrequency(PIN_BUZZER_TONE, freq);
        analogWrite(PIN_BUZZER_TONE, 256);  // 50% duty cycle (9-bit: 512/2 = 256)
    }
    // Amplitude controls volume via separate pin
    // Scaled by 4 for 9-bit PWM (0-511)
    analogWrite(PIN_BUZZER_AMP, amp * 2);
}

void buzzer_stop() // stop the buzzer
{
    analogWrite(PIN_BUZZER_TONE, 0);  // Stop tone
    analogWrite(PIN_BUZZER_AMP, 0);   // Stop amplitude
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

    // VIB2 unused
    // pinMode(PIN_VIB2_PWM, OUTPUT);
    // analogWriteFrequency(PIN_VIB2_PWM, 46875);
    // pinMode(PIN_VIB2_PH, OUTPUT);

    pinMode(PIN_BUZZER_TONE, OUTPUT);
    pinMode(PIN_BUZZER_AMP, OUTPUT);
    analogWriteFrequency(PIN_BUZZER_AMP, 292968);
    pinMode(LED_BUILTIN, OUTPUT);
    // Buzzer starts off
    analogWrite(PIN_BUZZER_TONE, 0);
    analogWrite(PIN_BUZZER_AMP, 0);

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
            if (source == 'v' || source == 'b') expected_len = 5;  // 'w' (vib2) unused
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
            // VIB2 unused
            // case 'w':
            // {
            //     ampVib2 = buff[0];
            //     uint16_t freqVib2 = *((uint16_t *)&buff[1]);
            //     periodVib2 = (freqVib2 > 0) ? (1000000 / freqVib2) : 0;
            //     start_us_vib2 = micros_time;
            //     end_us_vib2 = micros_time + *((uint16_t *)&buff[3]) * ((unsigned long)1000);
            //     vib2_state = true;
            //     break;
            // }
            case 'b':                                       // trigger a pulse for the buzzer
            {
                ampBuzz = buff[0];                          // read the amplitude of the buzzer
                freqBuzz = *((uint16_t *)&buff[1]);         // read the frequency (2 bytes)
                start_us_buzz = micros_time;
                end_us_buzz = micros_time + *((uint16_t *)&buff[3]) * ((unsigned long)1000);
                buzzer_start(ampBuzz, freqBuzz);            // start buzzer with hardware PWM
                buzz_state = true;
                break;
            }
            case 'c':                                       // combination of Buzzer and Vibration1
            {
                // Vibration 1
                ampVib1 = buff[0];                          // read the amplitude of the vibration1
                uint16_t freqVib1 = *((uint16_t *)&buff[1]); // read the frequency (2 bytes)
                periodVib1 = (freqVib1 > 0) ? (1000000 / freqVib1) : 0; // calculate the period in microseconds
                start_us_vib1 = micros_time;
                end_us_vib1 = micros_time + *((uint16_t *)&buff[3]) * ((unsigned long)1000);
                vib1_state = true;
                // Buzzer
                ampBuzz = buff[5];                          // read the amplitude of the buzzer
                freqBuzz = *((uint16_t *)&buff[6]);         // read the frequency (2 bytes)
                start_us_buzz = micros_time;
                end_us_buzz = micros_time + *((uint16_t *)&buff[8]) * ((unsigned long)1000);
                buzzer_start(ampBuzz, freqBuzz);            // start buzzer with hardware PWM
                buzz_state = true;
                break;
            }
            default:
                break;
            }
        }
    }
}