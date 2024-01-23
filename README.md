# Bsens
Simple device to trigger audio and haptic feedback for prenatanal studies

## Hardware

### Parts


| Part | Quantity | Price | Link |
| ---- | -------- | ----- | ---- |
| Arduino Mega 2560 | 1 | £30 | [Link](https://store.arduino.cc/arduino-mega-2560-rev3) |
| H-brige -  L298N | 1 | £2 | [Link](https://www.amazon.co.uk/Driver-H-Bridge-Stepper-Controller-Arduino/dp/B07YC1GFM3/ref=sr_1_6?crid=TGY74KFTE5R9&keywords=h+bridge&qid=1702907659&sprefix=h+br%2Caps%2C50&sr=8-6) |
| LRA - VG0640001D | 1 | £2 | [Link](https://www.digikey.co.uk/en/products/detail/vybronics-inc/VG0640001D/15220805) |
| STspin250 dev board | 1 | £15 | [Link](https://www.mikroe.com/stspin250-click) |
| Buzzer | 1 | £5 | [Link](https://www.amazon.co.uk/dp/B096ZWCG7F?psc=1&ref=ppx_yo2ov_dt_b_product_details) |
| Pressure sensor - ? | 1 | £5 | [Link](https://?) |
| GX16-5 Connector | 5 | £1.5 | [Link](https://www.amazon.co.uk/gp/product/B07WPBXX57/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) |
| USB-B Connector | 1 | £6.5 | [Link](https://www.amazon.co.uk/gp/product/B075FVGH8H/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1) |

| Total | ~ £70 |
| ----- | ---- |


### Diagram

![Diagram](docs/schematics.drawio.svg)

### 3D Model

| Name | File |
| ---- | ---- |
| Box | [Link](docs/box.stl) |
| Lid | [Link](docs/lid.stl) |

![Box](docs/render.png)

## Software

The GUI is written in Python and let you select 4 different existing experiments or open a custom one. 
You can then RUN, STOP and PAUSE the experiment. Each time a experiment is run, a new log file is created. 
The Log file contains the subject ID, the experiment name, the date and time of the experiment and the feedbacks given to the subject with a timestamp.

### Experiment rule file

The experiment rule file is a JSON file that contains the sequence of feedbacks or delays to be given to the subject.

| Type | Description | Attributes |
| ---- | ----------- | ---------- |
| Sequence | A sequence of feedbacks or delays | <b>Repeat</b>: number of time the sequence is repeated <br> <b>Content</b>: list of feedbacks or delays |
| Feedback | A feedback to be given to the subject | <b>Content</b>: list of feedbacks (see below) |
| Vib1 | A vibration feedback | <b>Duration</b>: duration of the vibration (s) <br> <b>Deviation</b>: Random uniform deviation of the duration (s) |
| Vib2 | A vibration feedback | <b>Duration</b>: duration of the vibration (s) <br> <b>Deviation</b>: Random uniform deviation of the duration (s) |
| Buzzer | A buzzer feedback | <b>Duration</b>: duration of the buzzer (s) <br> <b>Deviation</b>: Random uniform deviation of the duration (s) |
| Delay | A delay between two feedbacks | <b>Duration</b>: duration of the delay (s) <br> <b>Deviation</b>: Random uniform deviation of the duration (s) |
| Dropout_sequence | A sequence of feedbacks or delays with dropout | <b>Repeat</b>: number of time the sequence is repeated <br> <b>Number_drop</b>: number of dropout in the sequence <br> <b>Content</b>: list of feedbacks or delays <br> <b>Dropout_content</b>: list of feedbacks or delays to be given during the dropout |


**Example**
```JSOM
{
    "Type": "Sequence",
    "Repeat": 2,
    "Content": [
        {
            "Type": "Sequence",
            "Repeat": 2,
            "Content": [
                {
                    "Type": "Feedback",
                    "Content": [
                        {
                            "Type": "Vib2",
                            "Duration": 1,
                            "Deviation": 0
                        }
                    ]
                },
                {
                    "Type": "Delay",
                    "Duration": 2,
                    "Deviation": 0
                }
            ]
        },
        {
            "Type": "Sequence",
            "Repeat": 1,
            "Content": [
                {
                    "Type": "Sequence",
                    "Repeat": 5,
                    "Content": [
                        {
                            "Type": "Feedback",
                            "Content": [
                                {
                                    "Type": "Vib2",
                                    "Duration": 1,
                                    "Deviation": 0
                                }
                            ]
                        },
                        {
                            "Type": "Delay",
                            "Duration": 4,
                            "Deviation": 0
                        }
                    ]
                },
                {
                    "Type": "Dropout_sequence",
                    "Repeat": 5,
                    "Number_drop": 2,
                    "Content": [
                        {
                            "Type": "Feedback",
                            "Content": [
                                {
                                    "Type": "Vib2",
                                    "Duration": 1,
                                    "Deviation": 0
                                }
                            ]
                        },
                        {
                            "Type": "Delay",
                            "Duration": 1,
                            "Deviation": 0
                        }
                    ],
                    "Dropout_content": [
                        {
                            "Type": "Delay",
                            "Duration": 3,
                            "Deviation": 0
                        }
                    ]
                }
            ]
        }

    ]
}
```