
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
    # Canonical key names (lowercase -> canonical)
    _KEY_MAP = {
        # Rule types
        "type": "Type",
        "sequence": "Sequence",
        "stimulus": "stimulus",  # kept lowercase for backwards compat
        "delay": "Delay",
        "dropout_sequence": "Dropout_sequence",
        "randomized_sequence": "Randomized_sequence",
        # Stimulus types
        "buzzer": "Buzzer",
        "vib1": "Vib1",
        "vib2": "Vib2",
        "buzzvib1": "BuzzVib1",
        # Common fields
        "repeat": "Repeat",
        "content": "Content",
        "duration": "Duration",
        "deviation": "Deviation",
        "amplitude": "Amplitude",
        "frequency": "Frequency",
        "tone": "Tone",
        "label": "Label",
        # Dropout_sequence fields
        "number_drop": "Number_drop",
        "dropout_content": "Dropout_content",
        # Randomized_sequence fields
        "max_consecutive": "Max_consecutive",
        "stimuli": "Stimuli",
        # BuzzVib1 fields
        "amplitude_vib1": "Amplitude_vib1",
        "frequency_vib1": "Frequency_vib1",
        "duration_vib1": "Duration_vib1",
        "amplitude_buzz": "Amplitude_buzz",
        "tone_buzz": "Tone_buzz",
        "duration_buzz": "Duration_buzz",
        "deviation_amplitude_vib1": "Deviation_amplitude_vib1",
        "deviation_duration_vib1": "Deviation_duration_vib1",
        "deviation_amplitude_buzz": "Deviation_amplitude_buzz",
        "deviation_tone_buzz": "Deviation_tone_buzz",
        "deviation_duration_buzz": "Deviation_duration_buzz",
        "deviation_tone": "Deviation_tone",
        "deviation_duration": "Deviation_duration",
    }

    def __init__(self):
        # Experiment initialization
        self.log_cb = self.__default_cb
        self.event_cb = self.__default_cb
        self.arduino = ArduinoCom()
        self._lock = threading.Lock()  # protects shared state
        self._sequence = []
        self._current_idx = 0
        self._running = False
        self._stop_event = threading.Event()  # for fast interrupt of delays
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
        self._stop_event.set()  # interrupt any ongoing delay
        self.thread.join(timeout=2.0)
        self.arduino.disconnect()  # clean up serial connection

    def connect_arduino(self, path):
        self.arduino.connect(path)

    def add_cb_log(self, cb):
        self.log_cb = cb

    def add_cb_event(self, cb):
        self.event_cb = cb

    def start(self):
        self._stop_event.clear()  # reset stop event
        self.running = True

    def stop(self):
        with self._lock:
            self._running = False
            self._current_idx = 0
        self._stop_event.set()  # interrupt any ongoing delay immediately

    def pause(self):
        self.running = False
        self._stop_event.set()  # interrupt any ongoing delay

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
        elif rule_type == "Randomized_sequence":
            return self.__read_randomized_sequence(rules)
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

    def __read_randomized_sequence(self, rules):
        """Read a randomized sequence with max consecutive constraint.

        Example JSON:
        {
            "Type": "Randomized_sequence",
            "Max_consecutive": 3,
            "Delay": {"Type": "Delay", "Duration": 2, "Deviation": 0.5},
            "Stimuli": [
                {"Repeat": 20, "Label": "33%", "Content": {"Type": "Vib1", ...}},
                {"Repeat": 20, "Label": "66%", "Content": {"Type": "Vib1", ...}},
                {"Repeat": 20, "Label": "100%", "Content": {"Type": "Vib1", ...}}
            ]
        }
        """
        for field in ("Max_consecutive", "Stimuli"):
            if field not in rules:
                raise ValueError(f"Randomized_sequence requires '{field}' field")

        max_consec = rules["Max_consecutive"]
        stimuli_defs = rules["Stimuli"]
        delay_def = rules.get("Delay", None)

        if not isinstance(stimuli_defs, list) or len(stimuli_defs) < 2:
            raise ValueError("Randomized_sequence 'Stimuli' must be a list with at least 2 items")
        if not isinstance(max_consec, int) or max_consec < 1:
            raise ValueError("Randomized_sequence 'Max_consecutive' must be a positive integer")

        # Build list of (stimulus_index, stimulus_def) for each repeat
        all_stimuli = []
        for stim_idx, stim_def in enumerate(stimuli_defs):
            if "Repeat" not in stim_def or "Content" not in stim_def:
                raise ValueError(f"Stimuli[{stim_idx}] requires 'Repeat' and 'Content' fields")
            repeat_count = stim_def["Repeat"]
            label = stim_def.get("Label", f"Stim{stim_idx}")
            for _ in range(repeat_count):
                all_stimuli.append((stim_idx, stim_def["Content"], label))

        # Shuffle with max consecutive constraint
        shuffled = self.__shuffle_with_constraint(all_stimuli, max_consec)

        # Log the randomized order for reproducibility
        order_str = "".join(str(s[0]) for s in shuffled)
        self.log_cb(f"Randomized order ({len(shuffled)} stimuli): {order_str}")

        # Build the final sequence
        arr = []
        for i, (stim_idx, content, label) in enumerate(shuffled):
            # Parse the stimulus content
            stim_events = self.__read_type({"Type": "stimulus", "Content": [content]})
            # Update label to include the original label
            for event in stim_events:
                event[1] = f"{label}"
            arr.extend(stim_events)

            # Add delay between stimuli (except after the last one)
            if delay_def is not None and i < len(shuffled) - 1:
                arr.extend(self.__read_type(delay_def))

        return arr

    def __shuffle_with_constraint(self, items, max_consecutive, max_attempts=1000):
        """Shuffle items ensuring no value appears more than max_consecutive times in a row.

        Args:
            items: List of (index, content, label) tuples
            max_consecutive: Maximum allowed consecutive items with same index
            max_attempts: Maximum shuffle attempts before giving up

        Returns:
            Shuffled list satisfying the constraint
        """
        for attempt in range(max_attempts):
            shuffled = items[:]
            random.shuffle(shuffled)

            if self.__check_consecutive_constraint(shuffled, max_consecutive):
                return shuffled

            # Try to fix violations by swapping
            shuffled = self.__fix_consecutive_violations(shuffled, max_consecutive)
            if self.__check_consecutive_constraint(shuffled, max_consecutive):
                return shuffled

        # If we couldn't satisfy constraint, log warning and return best effort
        self.log_cb(f"Warning: Could not satisfy Max_consecutive={max_consecutive} after {max_attempts} attempts")
        return shuffled

    def __check_consecutive_constraint(self, items, max_consecutive):
        """Check if no index appears more than max_consecutive times in a row."""
        if len(items) <= 1:
            return True

        consecutive_count = 1
        prev_idx = items[0][0]

        for i in range(1, len(items)):
            curr_idx = items[i][0]
            if curr_idx == prev_idx:
                consecutive_count += 1
                if consecutive_count > max_consecutive:
                    return False
            else:
                consecutive_count = 1
            prev_idx = curr_idx

        return True

    def __fix_consecutive_violations(self, items, max_consecutive):
        """Attempt to fix consecutive violations by swapping elements."""
        items = items[:]  # work on a copy
        n = len(items)

        for _ in range(n * 2):  # limit iterations
            # Find first violation
            violation_pos = -1
            consecutive_count = 1
            prev_idx = items[0][0]

            for i in range(1, n):
                curr_idx = items[i][0]
                if curr_idx == prev_idx:
                    consecutive_count += 1
                    if consecutive_count > max_consecutive:
                        violation_pos = i
                        break
                else:
                    consecutive_count = 1
                prev_idx = curr_idx

            if violation_pos == -1:
                break  # no violations found

            # Find a position to swap with (different index, not creating new violation)
            violation_idx = items[violation_pos][0]
            for swap_pos in range(n):
                if swap_pos == violation_pos:
                    continue
                if items[swap_pos][0] == violation_idx:
                    continue

                # Check if swap would be valid
                items[violation_pos], items[swap_pos] = items[swap_pos], items[violation_pos]

                # Quick check around both positions
                valid = True
                for check_pos in [violation_pos, swap_pos]:
                    start = max(0, check_pos - max_consecutive)
                    end = min(n, check_pos + max_consecutive + 1)
                    count = 1
                    for j in range(start + 1, end):
                        if items[j][0] == items[j-1][0]:
                            count += 1
                            if count > max_consecutive:
                                valid = False
                                break
                        else:
                            count = 1
                    if not valid:
                        break

                if valid:
                    break  # keep the swap
                else:
                    # undo swap
                    items[violation_pos], items[swap_pos] = items[swap_pos], items[violation_pos]

        return items

    def __stimulus(self, signal):
        # Stimulus logic
        try:
            self.arduino.send_signal(signal)
            self.log_cb("stimulus: " + str(signal))
        except Exception as e:
            self.log_cb(f"stimulus error: {e}")
            self.stop()  # Stop experiment on communication error
    
    def __delay(self, value):
        delay_seconds = value[1]
        self.log_cb(f"delay: {delay_seconds}")
        # Use event.wait() for interruptible delay - returns immediately if stop_event is set
        self._stop_event.wait(timeout=delay_seconds)
    
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
        # Normalize keys to canonical form (case-insensitive)
        rules = self.__normalize(rules)
        # Validate schema first (catches errors before playback)
        self.__validate_schema(rules)
        self.sequence = self.__read_type(rules)
        self.current_idx = 0

    def __normalize(self, obj):
        """Recursively normalize dictionary keys and type values to canonical form.

        This makes the protocol case-insensitive, so users can write:
        - "type": "sequence" instead of "Type": "Sequence"
        - "AMPLITUDE": 0.5 instead of "Amplitude": 0.5
        """
        if isinstance(obj, dict):
            normalized = {}
            for key, value in obj.items():
                # Normalize key
                canonical_key = self._KEY_MAP.get(key.lower(), key)
                # Recursively normalize value
                normalized_value = self.__normalize(value)
                # Special handling for "Type" values - normalize them too
                if canonical_key == "Type" and isinstance(normalized_value, str):
                    normalized_value = self._KEY_MAP.get(normalized_value.lower(), normalized_value)
                normalized[canonical_key] = normalized_value
            return normalized
        elif isinstance(obj, list):
            return [self.__normalize(item) for item in obj]
        else:
            return obj

    def __validate_schema(self, rules, path="root"):
        """Validate JSON schema recursively. Raises ValueError with path on error."""
        if not isinstance(rules, dict):
            raise ValueError(f"Expected object at {path}, got {type(rules).__name__}")
        if "Type" not in rules:
            raise ValueError(f"Missing 'Type' field at {path}")

        rule_type = rules["Type"]

        if rule_type == "Sequence":
            if "Repeat" not in rules:
                raise ValueError(f"Sequence missing 'Repeat' at {path}")
            if not isinstance(rules["Repeat"], int) or rules["Repeat"] < 0:
                raise ValueError(f"Sequence 'Repeat' must be non-negative integer at {path}")
            if "Content" not in rules:
                raise ValueError(f"Sequence missing 'Content' at {path}")
            if not isinstance(rules["Content"], list):
                raise ValueError(f"Sequence 'Content' must be a list at {path}")
            for i, item in enumerate(rules["Content"]):
                self.__validate_schema(item, f"{path}.Content[{i}]")

        elif rule_type == "stimulus":
            if "Content" not in rules:
                raise ValueError(f"stimulus missing 'Content' at {path}")
            if not isinstance(rules["Content"], list):
                raise ValueError(f"stimulus 'Content' must be a list at {path}")
            for i, fb in enumerate(rules["Content"]):
                self.__validate_stimulus_item(fb, f"{path}.Content[{i}]")

        elif rule_type == "Delay":
            if "Duration" not in rules:
                raise ValueError(f"Delay missing 'Duration' at {path}")
            if not isinstance(rules["Duration"], (int, float)):
                raise ValueError(f"Delay 'Duration' must be a number at {path}")

        elif rule_type == "Dropout_sequence":
            for field in ("Number_drop", "Repeat", "Content", "Dropout_content"):
                if field not in rules:
                    raise ValueError(f"Dropout_sequence missing '{field}' at {path}")
            if rules["Number_drop"] > rules["Repeat"]:
                raise ValueError(f"Number_drop cannot exceed Repeat at {path}")
            if not isinstance(rules["Content"], list):
                raise ValueError(f"Dropout_sequence 'Content' must be a list at {path}")
            if not isinstance(rules["Dropout_content"], list):
                raise ValueError(f"Dropout_sequence 'Dropout_content' must be a list at {path}")
            for i, item in enumerate(rules["Content"]):
                self.__validate_schema(item, f"{path}.Content[{i}]")
            for i, item in enumerate(rules["Dropout_content"]):
                self.__validate_schema(item, f"{path}.Dropout_content[{i}]")

        elif rule_type == "Randomized_sequence":
            for field in ("Max_consecutive", "Stimuli"):
                if field not in rules:
                    raise ValueError(f"Randomized_sequence missing '{field}' at {path}")
            if not isinstance(rules["Max_consecutive"], int) or rules["Max_consecutive"] < 1:
                raise ValueError(f"Randomized_sequence 'Max_consecutive' must be positive integer at {path}")
            if not isinstance(rules["Stimuli"], list) or len(rules["Stimuli"]) < 2:
                raise ValueError(f"Randomized_sequence 'Stimuli' must be list with at least 2 items at {path}")
            for i, stim in enumerate(rules["Stimuli"]):
                if not isinstance(stim, dict):
                    raise ValueError(f"Stimuli[{i}] must be an object at {path}")
                if "Repeat" not in stim:
                    raise ValueError(f"Stimuli[{i}] missing 'Repeat' at {path}")
                if "Content" not in stim:
                    raise ValueError(f"Stimuli[{i}] missing 'Content' at {path}")
                if not isinstance(stim["Repeat"], int) or stim["Repeat"] < 1:
                    raise ValueError(f"Stimuli[{i}] 'Repeat' must be positive integer at {path}")
                self.__validate_stimulus_item(stim["Content"], f"{path}.Stimuli[{i}].Content")
            # Validate optional Delay
            if "Delay" in rules:
                self.__validate_schema(rules["Delay"], f"{path}.Delay")

        else:
            raise ValueError(f"Unknown type '{rule_type}' at {path}")

    def __validate_stimulus_item(self, fb, path):
        """Validate a single stimulus content item."""
        if not isinstance(fb, dict):
            raise ValueError(f"Expected object at {path}, got {type(fb).__name__}")
        if "Type" not in fb:
            raise ValueError(f"stimulus item missing 'Type' at {path}")

        fb_type = fb["Type"]

        if fb_type == "Buzzer":
            if "Amplitude" not in fb:
                raise ValueError(f"Buzzer missing 'Amplitude' at {path}")

        elif fb_type in ("Vib1", "Vib2"):
            for field in ("Amplitude", "Frequency", "Duration"):
                if field not in fb:
                    raise ValueError(f"{fb_type} missing '{field}' at {path}")

        elif fb_type == "BuzzVib1":
            for field in ("Amplitude_vib1", "Frequency_vib1", "Duration_vib1", "Amplitude_buzz"):
                if field not in fb:
                    raise ValueError(f"BuzzVib1 missing '{field}' at {path}")

        else:
            raise ValueError(f"Unknown stimulus type '{fb_type}' at {path}")

    def run(self):
        # Experiment logic
        pass
