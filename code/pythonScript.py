"""script connecting to the ardiuno and sending data to it"""
import serial
import time

#a signal is composed of:
# - vibration intensity [0,1]
# - a tone intensity [0,1]
# - a duration in centiseconds [0, 255]
sequence = [(0, 1, 100), (1, 0,0), (1, 1, 10), (0, 0, 0)]
interval = 2 #interval between each signal in seconds
loop_number = 2 #number of times the sequence is repeated

#connect to the arduino
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2) #wait for the arduino to be ready

def send_signal(signal):
    """send a signal to the arduino"""
    vib = int(signal[0]*255).to_bytes(1, byteorder='big', signed=False)
    vib2 = int(0).to_bytes(1, byteorder='big', signed=False)
    tone = int(signal[1]*255).to_bytes(1, byteorder='big', signed=False)
    duration = max(0, min(255, int(signal[2]))).to_bytes(1, byteorder='big', signed=False)
    cmd = vib+ vib2 + tone + duration
    arduino.write(cmd)
    time.sleep(signal[2]/100)
    ans = arduino.read(1) #wait for the arduino to be ready
    #check if the ans is equal to the sum of the bytes sent
    if ans != (sum(cmd)%256).to_bytes(1, byteorder='big', signed=False):
        print("error in the communication")
        print("cmd sent: ", cmd)
        print("ans: ", ans)
    

id_loop = 0
while id_loop < loop_number:
    for signal in sequence:
        send_signal(signal)
        print("signal sent: ", signal)
        time.sleep(interval)
    id_loop += 1