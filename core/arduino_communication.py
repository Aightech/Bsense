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
            self.arduino = serial.Serial(path, 9600, timeout=1)
            time.sleep(2)
        except:
            raise Exception("Arduino not found at " + path)

    def send_signal(self, signal):
        """Send a signal to the Arduino
        signal is a tuple:
        - vibration intensity [0,1]
        - a tone intensity [0,1]
        - a duration in centiseconds [0, 255]
        """
        # vib = int(signal[0]*255).to_bytes(1, byteorder='big', signed=False)
        # vib2 = int(0).to_bytes(1, byteorder='big', signed=False)
        # tone = int(signal[1]*255).to_bytes(1, byteorder='big', signed=False)
        # duration = max(0, min(255, int(signal[2]))).to_bytes(1, byteorder='big', signed=False)
        # cmd = vib+ vib2 + tone + duration
        # self.arduino.write(cmd)
        # time.sleep(signal[2]/100)
        # ans = self.arduino.read(1)
        # #check if the ans is equal to the sum of the bytes sent
        # if ans != (sum(cmd)%256).to_bytes(1, byteorder='big', signed=False):
        #     print("error in the communication")
        #     print("cmd sent: ", cmd)
        #     print("ans: ", ans)
            
