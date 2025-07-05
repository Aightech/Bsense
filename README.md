# Bsense

Simple device to trigger audio and haptic stimuli for prenatal studies.

## Hardware

### Components

| Part                  | Qty | Price | Link |
|-----------------------|-----|-------|------|
| Arduino Mega 2560     | 1   | £30   | [Arduino Mega 2560 Rev3](https://store.arduino.cc/arduino-mega-2560-rev3) |
| H-bridge (L298N)      | 1   | £2    | [Amazon UK](https://www.amazon.co.uk/Driver-H-Bridge-Stepper-Controller-Arduino/dp/B07YC1GFM3) |
| LRA (VG0640001D)      | 1   | £2    | [Digi-Key](https://www.digikey.co.uk/en/products/detail/vybronics-inc/VG0640001D/15220805) |
| LRA (VLV101040A)      | 1   | £5    | [Digi-Key](https://www.digikey.co.uk/en/products/detail/vybronics-inc/VLV101040A/12323590) |
| STSPIN250 dev board   | 1   | £15   | [MikroElektronika](https://www.mikroe.com/stspin250-click) |
| Buzzer                | 1   | £5    | [Amazon UK](https://www.amazon.co.uk/dp/B096ZWCG7F) |
| Pressure sensor       | 1   | £5    | *To be specified* |
| GX16-5 connector      | 5   | £1.50 | [Amazon UK](https://www.amazon.co.uk/gp/product/B07WPBXX57) |
| USB-B connector       | 1   | £6.50 | [Amazon UK](https://www.amazon.co.uk/gp/product/B075FVGH8H/) |

**Total cost:** ~£70

### Schematic

![System schematic](docs/schematics.drawio.svg)

### Enclosure

| Model  | File                  |
|--------|-----------------------|
| Box    | [docs/box.stl](docs/box.stl) |
| Lid    | [docs/lid.stl](docs/lid.stl) |

![Rendered enclosure](docs/render.png)

## Software

The GUI is written in Python 3 and CustomTkinter. It enables selection of four predefined experiments or a custom protocol, then controls Run, Pause and Stop operations. Each session generates a timestamped log file recording subject ID, protocol name, stimulus parameters and timestamps.

### Usage

1. **Connect**: enter serial port (e.g. `COM3` or `/dev/ttyUSB0`), click **Connect**.
2. **Validate subject**: input non-empty ID, click ✔.
3. **Select protocol**: choose from drop-down or browse JSON.
4. **Run**: click ▶ to start; use || to pause; ■ to stop.
5. **Log**: view live log; add manual annotations via bottom-left field.



### Experiment Protocol
The experiment protocol is defined in JSON format, allowing for flexible configuration of stimuli and delays. The protocol consists of nested sequences, each containing various types of stimuli and delays.

| Type                  | Description                        | Attributes                                                                                                                                      |
| --------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Sequence**          | Repeatable block of stimuli/delays | `Repeat` (int), `Content` (list of stimuli/delays)                                                                                              |
| **stimulus**          | Container for one or more stimuli  | `Content` (list of individual stimuli)                                                                                                          |
| **Vib1**  | Single vibration                   | `Amplitude` (0–1), `Frequency` (Hz), `Duration` (ms), `Deviation` (± uniform)                                                                   |
| **Buzzer**            | Audio tone                         | `Amplitude` (0–1), `Tone` (Hz), `Duration` (ms), `Deviation_tone`, `Deviation_duration`                                                         |
| **BuzzVib1**          | Combined buzzer + vibration        | `Amplitude_buzz`, `Deviation_amplitude_buzz`, `Tone_buzz`, `Deviation_tone_buzz`, `Duration_buzz`, `Amplitude_vib2`, `Deviation_amplitude_vib2` |
| **Delay**             | Pause                              | `Duration` (s), `Deviation` (± uniform)                                                                                                         |
| **Dropout\_sequence** | Sequence with random dropouts      | `Repeat` (int), `Number_drop` (int), `Content`, `Dropout_content`                                                                               |



## JSON protocol format

Look exemple in `app/python/config/`


### Installation - Python development

1. Clone repository.  
2. Create and activate virtual environment:
```bash
   python3 -m venv env
   source env/bin/activate       # Linux/macOS
   env\Scripts\activate          # Windows
```

3. Install dependencies:

```bash
pip install customtkinter
```
4. Ensure `core/experiment.py` and example JSON (`code/expCustom_rule.json`) are present.

5. Run the GUI:
```bash
python main.py
```


### Communication Protocol

```wavedrom
{
    signal: [
        { name: "Command header", wave: "x====...xxx", data: ["0xaa", "src", "len", "data [len bytes]"] },
        { name: "Vibration 1", wave: "x======.xx", data: ["0xaa","'v'", "4","Amp", "Freq", "Durati. ms"] },
        { name: "Buzzer", wave: "x======.xx", data: ["0xaa","'b'", "4","Amp", "Freq", "Durati. ms"] },
        { name: "Buzz + Vibration 1", wave: "x======.===.xx", data: ["0xaa","'c'", "6","A_V", "F_V", "Dur_V.ms", "A_B", "F_B", "Dur_B.ms"] }, 
    ]
}
```


### Example Matlab snippet

```matlab
% Initialise serial connection
port = "COM3";            % adjust to your port
baud = 115200;            % match Arduino Serial.begin()
s = serialport(port, baud);
flush(s);                 % clear buffer

START_CHAR = uint8(255);

% Send a vibration1 command
% amp: 0–255, freq: Hz (uint8), duration: ms (uint16)
function sendVib1(s, amp, freq, duration)
    payload = [...
        uint8(amp), ...
        uint8(freq), ...
        uint8(bitand(duration,255)), ...
        uint8(bitshift(duration,-8)) ...
    ];
    header = [START_CHAR; uint8('v'); uint8(numel(payload))];
    write(s, [header; payload], 'uint8');
end

% Send a buzzer command
function sendBuzz(s, amp, freq, duration)
    payload = [...
        uint8(amp), ...
        uint8(freq), ...
        uint8(bitand(duration,255)), ...
        uint8(bitshift(duration,-8)) ...
    ];
    header = [START_CHAR; uint8('b'); uint8(numel(payload))];
    write(s, [header; payload], 'uint8');
end

% Send combination of vibration1 + buzzer
function sendCombo(s, ampV, freqV, durV, ampB, freqB, durB)
    payload = [...
        uint8(ampV), ...
        uint8(freqV), ...
        uint8(bitand(durV,255)), ...
        uint8(bitshift(durV,-8)), ...
        uint8(ampB), ...
        uint8(freqB), ...
        uint8(bitand(durB,255)), ...
        uint8(bitshift(durB,-8)) ...
    ];
    header = [START_CHAR; uint8('c'); uint8(numel(payload))];
    write(s, [header; payload], 'uint8');
end

% Example usage:
% sendVib1(s, 128, 50, 500);      % vibration1: 50 Hz, 500 ms, amplitude 128
% sendBuzz(s, 200, 1000, 250);    % buzzer: 1 kHz, 250 ms, amplitude 200
% sendCombo(s, 100, 80, 300, 150, 500, 400); % combo: vib1 80 Hz, 300 ms, amp 100 + buzzer 500 Hz, 400 ms, amp 150
```