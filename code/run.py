#python script running a GUI for the user to interact with the program
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import customtkinter as ctk
import json
import random
import time
import serial

#global variables
name = "Bsense"
version = "1.0"
author = "Alexis Devillard"

w_width = 500
w_height = 500

exp_names = ["Experiment 1", "Experiment 2", "Experiment 3", "Experiment 4", "Experiment Custom"]
exp_rules = []

exp_rules.append({"Type": "Sequence", "Repeat": 10, "Content": [{"Type": "stimulus", "Content": [{"Type": "Vib2", "Amplitude": 1, "Deviation": 0}]}, {"Type": "Delay", "Duration": 10, "Deviation": 2}]})
exp_rules.append({"Type": "Sequence", "Repeat": 10, "Content": [{"Type": "stimulus", "Content": [{"Type": "Vib2", "Amplitude": 1, "Deviation": 0}]}, {"Type": "Delay", "Duration": 10, "Deviation": 0}, {"Type": "stimulus", "Content": [{"Type": "Vib2", "Amplitude": 1, "Deviation": 0}]}, {"Type": "Delay", "Duration": 10, "Deviation": 2}]})
exp_rules.append({"Type": "Sequence", "Repeat": 10, "Content": [{"Type": "stimulus", "Content": [{"Type": "Buzzer", "Amplitude": 1, "Deviation": 0}]}, {"Type": "Delay", "Duration": 10, "Deviation": 2}]})
exp_rules.append({"Type": "Sequence", "Repeat": 10, "Content": [{"Type": "stimulus", "Content": [{"Type": "Buzzer", "Amplitude": 1, "Deviation": 0}]}, {"Type": "Delay", "Duration": 10, "Deviation": 2}]})

current_exp_index = -1
current_exp = []
event_index = 0
exp_running = False
root = None

# #connect to the arduino
# arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
# time.sleep(2) #wait for the arduino to be ready

def send_signal(signal):
    """send a signal to the arduino
    signal is a tuple:
    - vibration intensity [0,1]
    - a tone intensity [0,1]
    - a duration in centiseconds [0, 255]
    """
    vib = int(signal[0]*255).to_bytes(1, byteorder='big', signed=False)
    vib2 = int(0).to_bytes(1, byteorder='big', signed=False)
    tone = int(signal[1]*255).to_bytes(1, byteorder='big', signed=False)
    duration = max(0, min(255, int(signal[2]))).to_bytes(1, byteorder='big', signed=False)
    cmd = vib+ vib2 + tone + duration
    # arduino.write(cmd)
    # time.sleep(signal[2]/100)
    # ans = arduino.read(1) #wait for the arduino to be ready
    # #check if the ans is equal to the sum of the bytes sent
    # if ans != (sum(cmd)%256).to_bytes(1, byteorder='big', signed=False):
    #     print("error in the communication")
    #     print("cmd sent: ", cmd)
    #     print("ans: ", ans)

def stimulus(signal):
    add_log("stimulus: " + str(signal))
    #send_signal(signal)

def delay(value):
    global exp_running
    add_log("delay: " + str(value))
    #wait for the delay while checking if the experiment is still running
    t0 = time.time()
    while time.time() - t0 < value/4 and exp_running:
        time.sleep(0.001)
    

def generate_experiment(path="custom_experiment.json"):
    try:
        #open the file
        print("Opening file " + path)
        print("Generating experiment")
        with open(path, "r") as f:
            rules = json.load(f)
            #parse the rules
            array_exp = read_type(rules)
            return array_exp
    except:
        print("Error: could not open file " + path)
        return []

def read_type(rules):
    if rules["Type"] == "Sequence":
        return read_sequence(rules)
    elif rules["Type"] == "stimulus":
        return read_stimulus(rules)
    elif rules["Type"] == "Delay":
        return read_delay(rules)
    elif rules["Type"] == "Dropout_sequence":
        return read_dropout_sequence(rules)
    else:
        print("Error: unknown type " + rules["Type"])  
        return []

def read_sequence(rules):
    arr = []
    for k in range(rules["Repeat"]):
        for i in range(len(rules["Content"])):
            arr += read_type(rules["Content"][i])
    return arr

def read_stimulus(rules):
    signal = 0
    arr = []
    for fb in rules["Content"]:
        if fb["Type"] == "Vib1" or fb["Type"] == "Vib2" or fb["Type"] == "Buzzer":
            signal = fb["Amplitude"]+fb["Deviation"]*(1-2*random.random())
            arr.append([lambda: stimulus(signal), fb["Type"], signal])
    return arr

def read_delay(rules):
    dt = rules["Duration"]+rules["Deviation"]*(1-2*random.random())
    return [[lambda: delay(dt), "Delay", dt]] 

def read_dropout_sequence(rules):
    if rules["Number_drop"] > rules["Repeat"]:
        print("Error: Number_drop > Repeat")
        return []
    else:
        idx = random.sample(range(rules["Repeat"]), rules["Number_drop"])
        for i in range(rules["Repeat"]):
            if i in idx:
                for k in range(len(rules["Dropout_content"])):
                    arr += read_type(rules["Dropout_content"][k])
            else:
                for k in range(len(rules["Content"])):
                    arr += read_type(rules["Content"][k])
    return arr
    

def on_button_GO_click():
    global exp_running
    add_log("GO")
    exp_running = True

def on_button_PAUSE_click():
    global exp_running
    add_log("PAUSE")
    exp_running = False

def on_button_STOP_click():
    global exp_running, event_index   
    add_log("STOP")
    exp_running = False
    event_index = 0
    
    
def add_log(text):
    global log_text
    #add time stamp + text + new line
    #timestamp = H:M:S:ms
    log_text.insert(tk.END, time.strftime("%H:%M:%S") + "[" + str(time.time()) + "] - " + text + "\n")
    
def exp_loop():
    global current_exp, event_index, exp_running, root, exp_treeview
    while root != None:
        #on_treeview_select({"widget": exp_treeview, "text": str(event_index)})
        if exp_running and event_index >= len(current_exp):
            event_index = 0
            exp_running = False
            add_log("End of experiment")
        if exp_running:
            exp_treeview.selection_set(exp_treeview.get_children()[event_index])
            current_exp[event_index][0]()
            if exp_running:#check if the experiment is still running and was not stopped during the execution of the event
                event_index += 1   
        else:
            time.sleep(0.1)
        
# Create the main window
root = ctk.CTk()
root.title("Bsense GUI (v" + version + ")")
#windows size
root.geometry("1200x400")

#create a global frame
global_frame = ctk.CTkFrame(root)
global_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
#create a frame for left side
left_frame = ctk.CTkFrame(global_frame)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0, pady=0)
#create a frame for right side
right_frame = ctk.CTkFrame(global_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0)

#add a treeview frame to the right frame
exp_treeview_frame = ctk.CTkFrame(right_frame)
exp_treeview_frame.pack(fill=tk.BOTH,side=tk.LEFT, expand=True, padx=0, pady=0)
#create label for the treeview
exp_treeview_label = ctk.CTkLabel(exp_treeview_frame, text="Experiments Configuration")
exp_treeview_label.pack(side=tk.TOP, padx=0, pady=0)
#create a treeview
exp_treeview = ttk.Treeview(exp_treeview_frame)
exp_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
#add columns to the treeview ("index", "event", "duration")
exp_treeview["columns"]=("event", "value")
#add the columns titles
exp_treeview.column("#0", width=50)
exp_treeview.column("event", width=100)
exp_treeview.column("value", width=100)
#add the columns headers
exp_treeview.heading("#0", text="id", anchor=tk.W)
exp_treeview.heading("event", text="Event", anchor=tk.W)
exp_treeview.heading("value", text="Value", anchor=tk.W)

#bind function when clicking on an item
def on_treeview_select(event):
    global event_index
    # get the index of the selected item
    item_iid = event.widget.selection()
    prev = event_index
    if exp_treeview.item(item_iid)["text"] != "":
        event_index = int(exp_treeview.item(item_iid)["text"])
        if prev != event_index:
            add_log("Jump to event: " + str(event_index))
exp_treeview.bind("<<TreeviewSelect>>", on_treeview_select)


#add a log frame to the right frame
log_frame = ctk.CTkFrame(right_frame)
log_frame.pack(fill=tk.BOTH,side=tk.LEFT, expand=True, padx=0, pady=0)
#create label for the log
log_label = ctk.CTkLabel(log_frame, text="Log")
log_label.pack(side=tk.TOP, padx=0, pady=0)
#create a text widget
log_text = tk.Text(log_frame)
log_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
#add a scroll bar to the text widget
log_scrollbar = tk.Scrollbar(log_frame)
log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_scrollbar.config(command=log_text.yview)
log_text.config(yscrollcommand=log_scrollbar.set)


# #create a button for the connection
connection_button = ctk.CTkButton(left_frame, text="Connect")
connection_button.pack(fill=tk.X, padx=10, pady=10)
#create a frame for Connection button
setting_frame = ctk.CTkFrame(left_frame)
setting_frame.pack(fill=tk.X, padx=10, pady=10)
#create a label for the title and place it in the frame
title_label = ctk.CTkLabel(setting_frame, text= "Subject: ")
title_label.pack(side=tk.LEFT, padx=0, pady=0)
#create a text entry and place it in the frame
subject_entry = tk.Entry(setting_frame)
subject_entry.pack(side=tk.LEFT, padx=0, pady=0, expand=True, fill=tk.X)
#add validation button
validation_button = ctk.CTkButton(setting_frame, text="Validate")
validation_button.pack(side=tk.LEFT, padx=10, pady=0)

#create a frame for combo box selecting the experiment
exp_frame = ctk.CTkFrame(left_frame)
exp_frame.pack(fill=tk.X, padx=10, pady=10)
combo_frame = ctk.CTkFrame(exp_frame)
combo_frame.pack(fill=tk.X, padx=10, pady=10)
#create a label for the combo box and place it in the frame
exp_label = ctk.CTkLabel(combo_frame, text="Experiment")
exp_label.pack(side=tk.LEFT, padx=0, pady=0)
#create a combo box and place it in the frame
exp_combo = tk.ttk.Combobox(combo_frame, values=exp_names)
exp_combo.pack(side=tk.LEFT, padx=10, pady=0, expand=True, fill=tk.X)
exp_combo.current(0)

#create a frame for the custom experiment button
custom_exp_frame = ctk.CTkFrame(exp_frame)
#create a label "path" and a text entry and a select button on the same line.
path_frame = ctk.CTkFrame(custom_exp_frame)
path_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=10)
path_label = ctk.CTkLabel(path_frame, text="Path")
path_label.pack(side=tk.LEFT, padx=10, pady=10)
path_entry = tk.Entry(path_frame)
path_entry.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
path_entry.insert(0, "expCustom_rule.json")

def on_path_browser_click():
    global current_exp, event_index
    filename = filedialog.askopenfilename(initialdir = "./",title = "Select file",filetypes = (("json files","*.json"),("all files","*.*")))
    path_entry.delete(0, tk.END)
    path_entry.insert(0, filename)
    current_exp = generate_experiment(filename)
    event_index = 0
    update_treeview(current_exp)
    add_log("Custom experiment: " + filename)
#create a Browse button
path_browser_button = ctk.CTkButton(path_frame, text="Browse", command=on_path_browser_click)
path_browser_button.pack(side=tk.LEFT, padx=10, pady=10)

def update_treeview(sequence):
    #delete all the items in the treeview
    exp_treeview.delete(*exp_treeview.get_children())
    #add the items
    for i in range(len(sequence)):
        exp_treeview.insert("", i, text=str(i), values=(sequence[i][1], round(sequence[i][2], 2)))
    #update the treeview
    exp_treeview.update_idletasks()
    if len(sequence) > 0:
        #set the selection to the first item
        exp_treeview.selection_set(exp_treeview.get_children()[0])
    

#make the custom experiment frame visible only if the custom experiment is selected
def on_combo_select(event):
    global current_exp
    current_exp_index = exp_combo.current()
    print("Experiment selected: " + exp_names[current_exp_index])
    add_log("Experiment selected: " + exp_names[current_exp_index])
    if exp_combo.get() == "Experiment Custom":
        #increase the size of the window
        root.update_idletasks()
        root.minsize(root.winfo_width(), root.winfo_height()+80)
        custom_exp_frame.pack(fill=tk.X, padx=10, pady=10)
    else:
        custom_exp_frame.pack_forget()
        root.update_idletasks()
        root.minsize(root.winfo_width(), root.winfo_height()-80)
    if current_exp_index < len(exp_rules):
        current_exp = read_type(exp_rules[current_exp_index])
        update_treeview(current_exp)
    else:
        current_exp = generate_experiment(path_entry.get())
        update_treeview(current_exp)
    
exp_combo.bind("<<ComboboxSelected>>", on_combo_select)
on_combo_select(None)



#create a frame for the commands buttons
command_frame = ctk.CTkFrame(left_frame)
command_frame.pack( fill=tk.X, expand=True, padx=10, pady=10)
command_label = ctk.CTkLabel(command_frame, text="Commands")
command_label.pack(side=tk.TOP, padx=0, pady=0)
command_buttons_frame = ctk.CTkFrame(command_frame)
command_buttons_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=10)
command_GO_button = ctk.CTkButton(command_buttons_frame, text="GO", command=on_button_GO_click)
command_GO_button.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
command_PAUSE_button = ctk.CTkButton(command_buttons_frame, text="PAUSE", command=on_button_PAUSE_click)
command_PAUSE_button.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
command_STOP_button = ctk.CTkButton(command_buttons_frame, text="STOP", command=on_button_STOP_click)
command_STOP_button.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)

#create a frame for exp_comments
comments_frame = ctk.CTkFrame(left_frame)
comments_frame.pack(fill=tk.X, padx=0, pady=0)
comments_label = ctk.CTkLabel(comments_frame, text="Log")
comments_label.pack(side=tk.LEFT, padx=10, pady=10)
comments_entry = tk.Entry(comments_frame)
comments_entry.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=10, expand=True)

def on_add_comment_click():
    global comments_entry
    add_log("Comment: " + comments_entry.get())
    comments_entry.delete(0, tk.END)

comments_button = ctk.CTkButton(comments_frame, text="Add", command=on_add_comment_click)
comments_button.pack(side=tk.LEFT, padx=10, pady=10)

#set minimum size of the window
root.update_idletasks()
#root.minsize(root.winfo_width(), root.winfo_height())

#start a thread for the experiment loop
import threading
exp_thread = threading.Thread(target=exp_loop)
exp_thread.start()


# Start the GUI event loop
root.mainloop()
root = None
exp_running = False
exit()


