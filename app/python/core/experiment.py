
import json
import random
import time
import threading
from core.arduino_communication import ArduinoCom


# def exp_loop():
#     global current_exp, event_index, exp_running, root, exp_treeview
#     while root != None:
#         #on_treeview_select({"widget": exp_treeview, "text": str(event_index)})
#         if exp_running and event_index >= len(current_exp):
#             event_index = 0
#             exp_running = False
#             add_log("End of experiment")
#         if exp_running:
#             exp_treeview.selection_set(exp_treeview.get_children()[event_index])
#             current_exp[event_index][0]()
#             if exp_running:#check if the experiment is still running and was not stopped during the execution of the event
#                 event_index += 1   
#         else:
#             time.sleep(0.1)
        

class Experiment:
    def __init__(self):
        # Experiment initialization
        self.log_cb = self.__default_cb
        self.event_cb = self.__default_cb
        self.arduino = ArduinoCom()
        self.sequence = []
        self.current_idx = 0
        self.running = False
        self.__active = True
        self.thread = threading.Thread(target=self.__main_loop)
        self.thread.start()
    
    def __default_cb(self, x):
        pass
    
    def close(self):
        self.__active = False
        self.running = False
        self.thread.join()
        
    def connect_arduino(self, path):
        self.arduino.connect(path)
    
    def add_cb_log(self, cb):
        self.log_cb = cb
        
    def add_cb_event(self, cb):
        self.event_cb = cb
        
    def start(self):
        self.running = True
        
    def stop(self):
        self.running = False
        self.current_idx = 0
        
    def pause(self):
        self.running = False
        
    def __main_loop(self):
        while self.__active:
            if self.running and self.current_idx >= len(self.sequence):
                self.running = False
                self.log_cb("End of experiment")
            if self.running:
                self.event_cb(self.current_idx)
                # print("kernel time: "+str(time.time()), self.sequence[self.current_idx][1])
                self.sequence[self.current_idx][0](self.sequence[self.current_idx][2])
                #print kernel time
                if self.running:#check if the experiment is still running and was not stopped during the execution of the event
                    self.current_idx += 1
            else:
                time.sleep(0.1)
    
    def __read_type(self, rules):
        if rules["Type"] == "Sequence":
            return self.__read_sequence(rules)
        elif rules["Type"] == "stimulus":
            return self.__read_stimulus(rules)
        elif rules["Type"] == "Delay":
            return self.__read_delay(rules)
        elif rules["Type"] == "Dropout_sequence":
            return self.__read_dropout_sequence(rules)
        else:
            print("Error: unknown type " + rules["Type"])  
            return []
        
    def __read_sequence(self, rules):
        arr = []
        for k in range(rules["Repeat"]):
            for i in range(len(rules["Content"])):
                arr += self.__read_type(rules["Content"][i])
        return arr
    
    def __read_stimulus(self, rules):
        signal = 0
        arr = []
        for fb in rules["Content"]:
            if fb["Type"] == "Buzzer":##Buzzer
                val = fb["Amplitude"]
                if "Deviation" in fb:
                    val += fb["Deviation"]*(1-2*random.random())
                val2 = 200
                dt = 500
                if "Tone" in fb:
                    val2 = fb["Tone"]
                    if "Deviation_tone" in fb:
                        val2 += fb["Deviation_tone"]*(1-2*random.random())
                if "Duration" in fb:
                    dt = fb["Duration"]
                    if "Deviation_duration" in fb:
                        dt += fb["Deviation_duration"]*(1-2*random.random())
                signal = ("b", val, val2, dt)

            elif fb["Type"] == "Vib1" or fb["Type"] == "Vib2":##Vib1 or Vib2
                val = fb["Amplitude"]
                freq = fb["Frequency"]
                dt = fb["Duration"]
                if "Deviation" in fb:
                    val += fb["Deviation"]*(1-2*random.random())
                source = "v" if fb["Type"] == "Vib1" else "w"
                signal = (source, val, freq, dt)

            elif fb["Type"] == "BuzzVib1": ##BuzzVib1
                ampVib1 = fb["Amplitude_vib1"]
                if "Deviation_amplitude_vib1" in fb:
                    ampVib1 += fb["Deviation_amplitude_vib1"]*(1-2*random.random())
                freqVib1 = fb["Frequency_vib1"]
                dtVib1 = fb["Duration_vib1"]
                if "Deviation_duration_vib1" in fb:
                    dtVib1 += fb["Deviation_duration_vib1"]*(1-2*random.random())
                
                ampBuzz = fb["Amplitude_buzz"]
                if "Deviation_amplitude_buzz" in fb:
                    ampBuzz += fb["Deviation_amplitude_buzz"]*(1-2*random.random())
                tone = 200
                dt = 500
                if "Tone_buzz" in fb:
                    tone = fb["Tone_buzz"]
                    if "Deviation_tone_buzz" in fb:
                        tone += fb["Deviation_tone_buzz"]*(1-2*random.random())
                if "Duration_buzz" in fb:
                    dt = fb["Duration_buzz"]
                    if "Deviation_duration_buzz" in fb:
                        dt += fb["Deviation_duration_buzz"]*(1-2*random.random())
                
                signal = ("c", ampVib1, freqVib1, dtVib1, ampBuzz, tone, dt)
                
            arr.append([self.__stimulus, fb["Type"], signal])
        return arr
    
    def __read_delay(self, rules):
        dt = rules["Duration"]+rules["Deviation"]*(1-2*random.random())
        return [[self.__delay, "Delay", [0,dt]]]
    
    def __read_dropout_sequence(self, rules):
        if rules["Number_drop"] > rules["Repeat"]:
            print("Error: Number_drop > Repeat")
            return []
        else:
            arr = []
            idx = random.sample(range(rules["Repeat"]), rules["Number_drop"])
            for i in range(rules["Repeat"]):
                if i in idx:
                    for k in range(len(rules["Dropout_content"])):
                        arr += self.__read_type(rules["Dropout_content"][k])
                else:
                    for k in range(len(rules["Content"])):
                        arr += self.__read_type(rules["Content"][k])
        return arr
    
    def __stimulus(self, signal):
        # Stimulus logic
        self.arduino.send_signal(signal)
        self.log_cb("stimulus: " + str(signal))
    
    def __delay(self, value):
        value = value[1]
        self.log_cb("delay: " + str(value))
        #wait for the delay while checking if the experiment is still running
        t0 = time.time()
        while time.time() - t0 < value and self.running:
            time.sleep(0.001)
    
    def from_json(self, path):
        # Load experiment from json file
        try:
            with open(path, "r") as f:
                self.from_dict(json.load(f))
        except:
            raise Exception("Error: could not open file " + path)
        
    def from_dict(self, rules):
        self.sequence = self.__read_type(rules)
        self.current_idx = 0

    def run(self):
        # Experiment logic
        pass
