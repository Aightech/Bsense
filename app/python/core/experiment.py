
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
        self._lock = threading.Lock()  # protects shared state
        self._sequence = []
        self._current_idx = 0
        self._running = False
        self.__active = True
        self.thread = threading.Thread(target=self.__main_loop, daemon=True)
        self.thread.start()

    @property
    def sequence(self):
        with self._lock:
            return self._sequence

    @sequence.setter
    def sequence(self, value):
        with self._lock:
            self._sequence = value

    @property
    def current_idx(self):
        with self._lock:
            return self._current_idx

    @current_idx.setter
    def current_idx(self, value):
        with self._lock:
            self._current_idx = value

    @property
    def running(self):
        with self._lock:
            return self._running

    @running.setter
    def running(self, value):
        with self._lock:
            self._running = value

    def __default_cb(self, x):
        pass

    def close(self):
        self.__active = False
        self.running = False
        self.thread.join(timeout=2.0)

    def connect_arduino(self, path):
        self.arduino.connect(path)

    def add_cb_log(self, cb):
        self.log_cb = cb

    def add_cb_event(self, cb):
        self.event_cb = cb

    def start(self):
        self.running = True

    def stop(self):
        with self._lock:
            self._running = False
            self._current_idx = 0

    def pause(self):
        self.running = False

    def __main_loop(self):
        while self.__active:
            with self._lock:
                is_running = self._running
                idx = self._current_idx
                seq_len = len(self._sequence)
                seq_copy = self._sequence[:]  # copy for safe iteration

            if is_running and idx >= seq_len:
                self.running = False
                self.log_cb("End of experiment")
            elif is_running:
                self.event_cb(idx)
                seq_copy[idx][0](seq_copy[idx][2])
                # check if still running after execution (might have been stopped)
                with self._lock:
                    if self._running:
                        self._current_idx += 1
            else:
                time.sleep(0.1)
    
    def __read_type(self, rules):
        if not isinstance(rules, dict) or "Type" not in rules:
            raise ValueError("Invalid rule: missing 'Type' field")
        rule_type = rules["Type"]
        if rule_type == "Sequence":
            return self.__read_sequence(rules)
        elif rule_type == "stimulus":
            return self.__read_stimulus(rules)
        elif rule_type == "Delay":
            return self.__read_delay(rules)
        elif rule_type == "Dropout_sequence":
            return self.__read_dropout_sequence(rules)
        else:
            raise ValueError(f"Unknown rule type: {rule_type}")
        
    def __read_sequence(self, rules):
        if "Repeat" not in rules or "Content" not in rules:
            raise ValueError("Sequence requires 'Repeat' and 'Content' fields")
        repeat = rules["Repeat"]
        content = rules["Content"]
        if not isinstance(repeat, int) or repeat < 0:
            raise ValueError("Sequence 'Repeat' must be a non-negative integer")
        if not isinstance(content, list):
            raise ValueError("Sequence 'Content' must be a list")
        arr = []
        for k in range(repeat):
            for item in content:
                arr += self.__read_type(item)
        return arr
    
    def __read_stimulus(self, rules):
        if "Content" not in rules or not isinstance(rules["Content"], list):
            raise ValueError("stimulus requires 'Content' list")
        signal = 0
        arr = []
        for fb in rules["Content"]:
            if not isinstance(fb, dict) or "Type" not in fb:
                raise ValueError("stimulus content item missing 'Type'")
            fb_type = fb["Type"]

            if fb_type == "Buzzer":
                if "Amplitude" not in fb:
                    raise ValueError("Buzzer requires 'Amplitude' field")
                val = fb["Amplitude"]
                val += fb.get("Deviation", 0) * (1 - 2 * random.random())
                val2 = fb.get("Tone", 200)
                val2 += fb.get("Deviation_tone", 0) * (1 - 2 * random.random())
                dt = fb.get("Duration", 500)
                dt += fb.get("Deviation_duration", 0) * (1 - 2 * random.random())
                signal = ("b", val, int(val2), int(dt))

            elif fb_type in ("Vib1", "Vib2"):
                for field in ("Amplitude", "Frequency", "Duration"):
                    if field not in fb:
                        raise ValueError(f"{fb_type} requires '{field}' field")
                val = fb["Amplitude"]
                val += fb.get("Deviation", 0) * (1 - 2 * random.random())
                freq = fb["Frequency"]
                dt = fb["Duration"]
                source = "v" if fb_type == "Vib1" else "w"
                signal = (source, val, int(freq), int(dt))

            elif fb_type == "BuzzVib1":
                for field in ("Amplitude_vib1", "Frequency_vib1", "Duration_vib1", "Amplitude_buzz"):
                    if field not in fb:
                        raise ValueError(f"BuzzVib1 requires '{field}' field")
                ampVib1 = fb["Amplitude_vib1"]
                ampVib1 += fb.get("Deviation_amplitude_vib1", 0) * (1 - 2 * random.random())
                freqVib1 = fb["Frequency_vib1"]
                dtVib1 = fb["Duration_vib1"]
                dtVib1 += fb.get("Deviation_duration_vib1", 0) * (1 - 2 * random.random())

                ampBuzz = fb["Amplitude_buzz"]
                ampBuzz += fb.get("Deviation_amplitude_buzz", 0) * (1 - 2 * random.random())
                tone = fb.get("Tone_buzz", 200)
                tone += fb.get("Deviation_tone_buzz", 0) * (1 - 2 * random.random())
                dt = fb.get("Duration_buzz", 500)
                dt += fb.get("Deviation_duration_buzz", 0) * (1 - 2 * random.random())

                signal = ("c", ampVib1, int(freqVib1), int(dtVib1), ampBuzz, int(tone), int(dt))
            else:
                raise ValueError(f"Unknown stimulus type: {fb_type}")

            arr.append([self.__stimulus, fb_type, signal])
        return arr
    
    def __read_delay(self, rules):
        if "Duration" not in rules:
            raise ValueError("Delay requires 'Duration' field")
        duration = rules["Duration"]
        deviation = rules.get("Deviation", 0)
        dt = duration + deviation * (1 - 2 * random.random())
        dt = max(0, dt)  # prevent negative delays
        return [[self.__delay, "Delay", [0, dt]]]
    
    def __read_dropout_sequence(self, rules):
        for field in ("Number_drop", "Repeat", "Content", "Dropout_content"):
            if field not in rules:
                raise ValueError(f"Dropout_sequence requires '{field}' field")
        num_drop = rules["Number_drop"]
        repeat = rules["Repeat"]
        if num_drop > repeat:
            raise ValueError(f"Number_drop ({num_drop}) cannot exceed Repeat ({repeat})")
        if not isinstance(rules["Content"], list) or not isinstance(rules["Dropout_content"], list):
            raise ValueError("Dropout_sequence 'Content' and 'Dropout_content' must be lists")
        arr = []
        idx = random.sample(range(repeat), num_drop)
        for i in range(repeat):
            if i in idx:
                for item in rules["Dropout_content"]:
                    arr += self.__read_type(item)
            else:
                for item in rules["Content"]:
                    arr += self.__read_type(item)
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
        except FileNotFoundError:
            raise Exception(f"Error: file not found: {path}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error: invalid JSON in {path}: {e}")
        except ValueError as e:
            raise Exception(f"Error: invalid experiment format in {path}: {e}")
        
    def from_dict(self, rules):
        self.sequence = self.__read_type(rules)
        self.current_idx = 0

    def run(self):
        # Experiment logic
        pass
