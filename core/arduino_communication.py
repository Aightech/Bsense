import serial
import time

class ArduinoCom:
    def __init__(self):
        # Arduino communication setup
        pass

    def connect(self, path):
        # Connect to Arduino
        self.path = path
        try:
            self.arduino = serial.Serial(path, 115200, timeout=1)
            time.sleep(2)
        except:
            raise Exception("Arduino not found at " + path)

    def send_signal(self, signal):
        """Send a signal to the Arduino
        signal is a tuple:
        - signal[0] is the source ['v', 'w', 'b'] vib1, vib2, buzzer
        - signal[1] is the value (0-255)
        - signal[2] is the second value (0-255)
        - signal[3-4] is the duration in 100us (0-65535)
        """
        #the cmd must start with 0xaa
        start = int(0xaa).to_bytes(1, byteorder='big', signed=False)
        #transform the char into bytes
        source = ord(signal[0]).to_bytes(1, byteorder='big', signed=False)
        val = int(signal[1]*255).to_bytes(1, byteorder='big', signed=False)
        val2 = int(signal[2]*255).to_bytes(1, byteorder='big', signed=False)
        dt = signal[3].to_bytes(2, byteorder='little', signed=False)
        cmd = start + source + val + val2 + dt
        # print("before send"+str(time.time()))
        self.arduino.write(cmd)
        # ans = self.arduino.read(6)
        # print("after send"+str(time.time()))
            
