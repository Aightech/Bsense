import serial
import time
import logging

logger = logging.getLogger(__name__)

class ArduinoCom:
    def __init__(self):
        # Arduino communication setup
        self.arduino = None
        pass

    def connect(self, path, retries=3, retry_delay=1.0):
        """Connect to Arduino with retry logic.

        Args:
            path: Serial port path (e.g., COM3, /dev/ttyUSB0)
            retries: Number of connection attempts (default: 3)
            retry_delay: Delay between retries in seconds (default: 1.0)
        """
        # Close existing connection if any
        self.disconnect()
        self.path = path
        last_error = None

        for attempt in range(retries):
            try:
                self.arduino = serial.Serial(path, 115200, timeout=1)
                time.sleep(2)  # Wait for Arduino to reset
                return  # Success
            except serial.SerialException as e:
                last_error = f"Arduino not found at {path}: {e}"
            except OSError as e:
                last_error = f"Cannot open port {path}: {e}"

            # Wait before retry (with exponential backoff)
            if attempt < retries - 1:
                time.sleep(retry_delay * (attempt + 1))

        raise Exception(last_error)

    def disconnect(self):
        """Close the serial connection if open."""
        if self.arduino is not None:
            try:
                self.arduino.close()
            except Exception:
                pass
            self.arduino = None

    def is_connected(self):
        """Check if serial port is open and connected."""
        return self.arduino is not None and self.arduino.is_open

    def send_signal(self, signal):
        """Send a signal to the Arduino
        signal is a tuple:
        - signal[0] is the source ['v', 'w', 'b', 'c'] vib1, vib2, buzzer, combined
        - signal[1] is the amplitude (0.0-1.0)
        - signal[2] is the frequency in Hz (0-65535)
        - signal[3] is the duration in ms (0-65535)
        For 'c' (combined): signal[4]=ampBuzz, signal[5]=freqBuzz, signal[6]=durBuzz
        """
        # Validate signal format
        if not isinstance(signal, (tuple, list)) or len(signal) < 1:
            raise ValueError("Signal must be a tuple/list with at least 1 element")
        if signal[0] not in ('v', 'w', 'b', 'c'):
            raise ValueError(f"Invalid signal type: {signal[0]}")
        if signal[0] in ('v', 'w', 'b') and len(signal) < 4:
            raise ValueError(f"Signal type '{signal[0]}' requires 4 elements (type, amp, freq, dur)")
        if signal[0] == 'c' and len(signal) < 7:
            raise ValueError("Signal type 'c' requires 7 elements (type, ampV, freqV, durV, ampB, freqB, durB)")

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
        cmd_hex = " ".join("{:02x}".format(c) for c in cmd)

        if self.arduino is not None:
            self.arduino.write(cmd)
            logger.debug(f"[SENT] cmd [{signal[0]}]: {cmd_hex} (len: {len(cmd)})")
        else:
            logger.warning(f"[UNSENT] cmd [{signal[0]}]: {cmd_hex} (len: {len(cmd)})")
            
