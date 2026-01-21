import serial
import time

class ArduinoCom:
    def __init__(self):
        # Arduino communication setup
        self.arduino = None
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
        - signal[0] is the source ['v', 'w', 'b', 'c'] vib1, vib2, buzzer, combined
        - signal[1] is the amplitude (0.0-1.0)
        - signal[2] is the frequency in Hz (0-65535)
        - signal[3] is the duration in ms (0-65535)
        For 'c' (combined): signal[4]=ampBuzz, signal[5]=freqBuzz, signal[6]=durBuzz
        """
        #the cmd must start with 0xaa
        start = int(0xaa).to_bytes(1, byteorder='big', signed=False)
        #transform the char into bytes
        source = ord(signal[0]).to_bytes(1, byteorder='big', signed=False)
        
        if signal[0] == 'b':
            #buzzer
            length = int(5).to_bytes(1, byteorder='big', signed=False)
            amp = int(max(0, min(255, signal[1]*255))).to_bytes(1, byteorder='big', signed=False)
            freq = int(signal[2]).to_bytes(2, byteorder='little', signed=False)
            dt = signal[3].to_bytes(2, byteorder='little', signed=False)
            buff = amp + freq + dt
        elif signal[0] == 'w' or signal[0] == 'v':
            #vib1 or vib2
            length = int(5).to_bytes(1, byteorder='big', signed=False)
            amp = int(max(0, min(255, signal[1]*255))).to_bytes(1, byteorder='big', signed=False)
            freq = int(signal[2]).to_bytes(2, byteorder='little', signed=False)
            dt = signal[3].to_bytes(2, byteorder='little', signed=False)
            buff = amp + freq + dt
        elif signal[0] == 'c':
            #combined buzz and vib1
            length = int(10).to_bytes(1, byteorder='big', signed=False)
            ampVib1 = int(max(0, min(255, signal[1]*255))).to_bytes(1, byteorder='big', signed=False)
            freqVib1 = int(signal[2]).to_bytes(2, byteorder='little', signed=False)
            dtVib1 = signal[3].to_bytes(2, byteorder='little', signed=False)
            ampBuzz = int(max(0, min(255, signal[4]*255))).to_bytes(1, byteorder='big', signed=False)
            freqBuzz = int(signal[5]).to_bytes(2, byteorder='little', signed=False)
            dtBuzz = signal[6].to_bytes(2, byteorder='little', signed=False)
            buff = ampVib1 + freqVib1 + dtVib1 + ampBuzz + freqBuzz + dtBuzz

        cmd = start + source + length + buff
        
        if self.arduino is not None:
            self.arduino.write(cmd)
            print("[SENT] cmd [" + signal[0] + "]: ", end="") 
            print(" ".join("{:02x}".format(c) for c in cmd), end="")
            print(" (len: " + str(len(cmd)) + ")")
        else:
            #print each byte of the command
            print("[UNSENT] cmd [" + signal[0] + "]: ", end="") 
            print(" ".join("{:02x}".format(c) for c in cmd), end="")
            print(" (len: " + str(len(cmd)) + ")")
            
