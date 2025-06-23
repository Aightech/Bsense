import tkinter as tk
import customtkinter as ctk

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import customtkinter as ctk
import threading
from core.experiment import Experiment
import time
#set theme
ctk.set_default_color_theme("dark-blue") 

class BsenseGUI(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        
        self.name = "Bsense"
        self.version = "1.0"
        self.author = "Alexis Devillard"

        self.in_debug_mode = False
        
        self.w_width = 1200
        self.w_height = 410
        
        self.exp_names = ["Experiment 1", "Experiment 2", "Experiment 3", "Experiment 4", "Experiment Custom"]
        self.exp_rules = []
        
        self.exp_rules.append({"Type":"Sequence","Repeat":10,"Content":[{"Type":"stimulus","Content":[{"Type":"Vib1","Amplitude":1,"Frequency":60,"Duration":13,"Deviation":0}]},{"Type":"Delay","Duration":2,"Deviation":0}]})

            
        self.current_exp_index = 0
        
        self.title(self.name + " " + self.version)
        self.geometry(str(self.w_width) + "x" + str(self.w_height))
        
        self.file_log_open = False
        
        self.exp = Experiment()
        self.exp.log_cb = self.add_log
        self.exp.event_cb = self.on_new_event

        self.setup_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def debug_mode(self):
        # Debug mode
        self.in_debug_mode = True
        #fill subject name
        self.subject_entry.insert(0, "test")
        #click ok
        self.on_button_validate_user_click()
    
    def set_port(self, port):
        self.connection_entry.delete(0, tk.END)
        self.connection_entry.insert(0, port)

    def set_file(self, file):
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, file)
        self.exp.from_json(file)
        self.update_treeview(self.exp.sequence)
        self.add_log("Custom experiment: " + file)

        

    def setup_ui(self):
        # Create frames
        self.global_frame = ctk.CTkFrame(self)
        self.global_frame.pack(fill=tk.BOTH, expand=True)

        self.left_frame = ctk.CTkFrame(self.global_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        self.right_frame = ctk.CTkFrame(self.global_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Add more UI components here
        self.create_experiment_treeview()
        self.create_log_frame()
        self.create_control_frame()
        
        #self.disable_controls()
        
    def run(self):
        self.mainloop()
        
    #when the window is closed
    def on_closing(self):
        print("closing")
        self.exp.close()
        if self.file_log_open:
            self.file_log.close()
        self.destroy()

    def create_experiment_treeview(self):
        # Treeview listing all the events
        self.exp_treeview_frame = ctk.CTkFrame(self.right_frame)
        self.exp_treeview_frame.pack(fill=tk.BOTH,side=tk.LEFT, padx=0, pady=0)
        #create label for the treeview
        self.exp_treeview_label = ctk.CTkLabel(self.exp_treeview_frame, text="Experiments Configuration")
        self.exp_treeview_label.pack(side=tk.TOP, padx=0, pady=0)
        #create a treeview
        self.exp_treeview = ttk.Treeview(self.exp_treeview_frame)
        
        # tree.insert('', 'end', text='button', tags=('ttk', 'simple'))
        # tree.tag_configure('ttk', background='yellow')
        # tree.tag_bind('ttk', '<1>', itemClicked)  
        # # the item clicked can be found via tree.f
        self.exp_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        #add columns to the treeview ("index", "event", "duration")
        self.exp_treeview["columns"]=("event", "value")
        #add the columns titles
        self.exp_treeview.column("#0", width=50)
        self.exp_treeview.column("event", width=100)
        self.exp_treeview.column("value", width=100)
        #add the columns headers
        self.exp_treeview.heading("#0", text="id", anchor=tk.W)
        self.exp_treeview.heading("event", text="Event", anchor=tk.W)
        self.exp_treeview.heading("value", text="Value", anchor=tk.W)
        self.exp_treeview.bind("<<TreeviewSelect>>", self.on_treeview_select)
        
    def on_treeview_select(self, event):
        # get the index of the selected item
        item_iid = event.widget.selection()[0]
        if self.exp_treeview.item(item_iid)["text"] != "":
            if not self.exp.running:
                new_idx = int(self.exp_treeview.item(item_iid)["text"])
                self.exp.current_idx = new_idx
                self.add_log("Jump to event: " + str(new_idx))
                
    def on_new_event(self, event):
        # call back function for the experiment
        # get the index of the selected item and update treeview
        #set the new active item in the treeview
        #print("new event" + str(event))
        self.exp_treeview.selection_set(self.exp_treeview.get_children()[self.exp.current_idx])
        
    def create_log_frame(self):
        # Frame for logs
        self.log_frame = ctk.CTkFrame(self.right_frame)
        self.log_frame.pack(fill=tk.BOTH,side=tk.LEFT, expand=True, padx=0, pady=0)
        #create label for the log
        self.log_label = ctk.CTkLabel(self.log_frame, text="Log")
        self.log_label.pack(side=tk.TOP, padx=0, pady=0)
        #create a text widget
        self.log_text = ctk.CTkTextbox(self.log_frame)
        self.log_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        

    def create_control_frame(self):
        """Frame for controls Connect, Validate user, Validate experiment, GO, PAUSE, STOP, ..."""
        #connect to the device button
        self.connection_frame = ctk.CTkFrame(self.left_frame, width=20)
        self.connection_frame.pack(side=tk.TOP, padx=0, pady=0, expand=True, fill=tk.BOTH)
        # self.connection_label = ctk.CTkLabel(self.connection_frame, text="Connection", width=20)
        # self.connection_label.pack(side=tk.TOP, padx=0, pady=0)
        self.device_frame = ctk.CTkFrame(self.connection_frame)
        self.device_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        self.connection_label = ctk.CTkLabel(self.device_frame, text="Device: ")
        self.connection_label.pack(side=tk.LEFT, padx=5, pady=0)
        self.connection_entry = ctk.CTkEntry(self.device_frame)
        self.connection_entry.insert(0, "COM3")
        self.connection_entry.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
        self.connection_button = ctk.CTkButton(self.device_frame, text="Connect", command=self.on_button_connect_click, width=10)
        self.connection_button.pack(side=tk.LEFT, padx=10, pady=10)
        #bind the click event to the entry
        self.connection_entry.bind("<Return>", self.on_button_connect_click)
        #bind the click event to the entry
        self.connection_entry.bind("<Button>", self.on_connection_entry_click)
    
        
        # Frame for controls
        self.control_frame = ctk.CTkFrame(self.left_frame, width=20)
        self.control_frame.pack(fill=tk.BOTH,side=tk.TOP, expand=True, padx=0, pady=0)
        #create label for the controls
        # self.control_label = ctk.CTkLabel(self.control_frame, text="Controls", width=20)
        # self.control_label.pack(side=tk.TOP, padx=0, pady=0)
        #create a frame for the connection
        self.subject_frame = ctk.CTkFrame(self.control_frame)
        self.subject_frame.pack(fill=tk.X, padx=10, pady=0)
        #create a label for the title and place it in the frame
        self.subject_label = ctk.CTkLabel(self.subject_frame, text= "Subject: ")
        self.subject_label.pack(side=tk.LEFT, padx=5, pady=0)
        #create a text entry and place it in the frame
        self.subject_entry = ctk.CTkEntry(self.subject_frame, width=10)#, state="disabled")
        self.subject_entry.pack(side=tk.LEFT, padx=0, pady=0, expand=True, fill=tk.X)
        
        #add validation button
        self.validation_button = ctk.CTkButton(self.subject_frame, text="✔", width=10, command=self.on_button_validate_user_click, state="disabled", fg_color="grey")
        self.validation_button.pack(side=tk.LEFT, padx=10, pady=5)
        

        #create a frame for combo box selecting the experiment
        self.exp_frame = ctk.CTkFrame(self.control_frame)
        self.exp_frame.pack(fill=tk.X, padx=10, pady=10,side=tk.TOP)
        self.combo_frame = ctk.CTkFrame(self.exp_frame)
        self.combo_frame.pack(fill=tk.X, padx=10, pady=10)
        #create a label for the combo box and place it in the frame
        self.exp_label = ctk.CTkLabel(self.combo_frame, text="Experiment", width=30)
        self.exp_label.pack(side=tk.LEFT, padx=5, pady=0)
        #create a combo box and place it in the frame
        self.exp_combo = ctk.CTkComboBox(self.combo_frame, values=self.exp_names, command=self.on_combo_select)
        self.exp_combo.pack(side=tk.LEFT, padx=10, pady=5, expand=True, fill=tk.X)
        
        #create a label "path" and a text entry and a select button on the same line.
        self.path_frame = ctk.CTkFrame(self.exp_frame)
        #self.path_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=10)
        self.path_label = ctk.CTkLabel(self.path_frame, text="Path")
        self.path_label.pack(side=tk.LEFT, padx=5, pady=0)
        self.path_entry = ctk.CTkEntry(self.path_frame)
        self.path_entry.pack(side=tk.LEFT, padx=5, pady=0, expand=True, fill=tk.X)
        self.path_entry.insert(0, "../code/expCustom_rule.json")
        self.path_browser_button = ctk.CTkButton(self.path_frame, text="Browse", command=self.on_path_browser_click)
        self.path_browser_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.on_combo_select(None)
        self.exp_combo.configure(state="disabled")
        
        #create a frame for the commands buttons
        self.command_frame = ctk.CTkFrame(self.control_frame, width=10)
        self.command_frame.pack( fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)
        self.command_label = ctk.CTkLabel(self.command_frame, text="Commands", width=10)
        self.command_label.pack(side=tk.TOP, padx=0, pady=0)
        self.command_buttons_frame = ctk.CTkFrame(self.command_frame, width=20)
        self.command_buttons_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=5)
        self.command_GO_button = ctk.CTkButton(self.command_buttons_frame, text="▶", command=self.on_button_GO_click, width=10, state="disabled", fg_color="grey")
        self.command_GO_button.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
        self.command_PAUSE_button = ctk.CTkButton(self.command_buttons_frame, text="||", command=self.on_button_PAUSE_click, width=10, state="disabled", fg_color="grey")
        self.command_PAUSE_button.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
        self.command_STOP_button = ctk.CTkButton(self.command_buttons_frame, text="■", command=self.on_button_STOP_click, width=10, state="disabled", fg_color="grey")
        self.command_STOP_button.pack(side=tk.LEFT, padx=10, pady=10, expand=True, fill=tk.X)
        
        
        #create a frame for exp_comments
        self.comments_frame = ctk.CTkFrame(self.control_frame, width=10)
        self.comments_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)
        self.comments_label = ctk.CTkLabel(self.comments_frame, text="Log")
        self.comments_label.pack(side=tk.LEFT, padx=10, pady=5)
        self.comments_entry = ctk.CTkEntry(self.comments_frame,width=20)
        self.comments_entry.pack(side=tk.LEFT, fill=tk.X, padx=5, pady=5, expand=True)
        self.comments_button = ctk.CTkButton(self.comments_frame, text="Add", command=self.on_add_comment_click, width=10)
        self.comments_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        
    def on_path_browser_click(self):
        filename = filedialog.askopenfilename(initialdir = "./",title = "Select file",filetypes = (("json files","*.json"),("all files","*.*")))
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, filename)
        self.exp.from_json(filename)
        self.event_index = 0
        self.update_treeview(self.exp.sequence)
        self.add_log("Custom experiment: " + filename)
    
    def on_combo_select(self, event):
        selected_exp = self.exp_combo.get()
        self.add_log("Experiment selected: " + selected_exp)
        print("selected exp: " + selected_exp)
        if selected_exp == "Experiment Custom" and self.current_exp_index < len(self.exp_rules):#if previous experiment was not custom
            #increase the size of the window
            self.update_idletasks()
            self.geometry(str(self.winfo_width()) + "x" + str(self.winfo_height()+80)+"+"+str(self.winfo_x())+"+"+str(self.winfo_y()-40))
            self.path_frame.pack(fill=tk.X, padx=10, pady=10)
        elif selected_exp != "Experiment Custom" and self.current_exp_index >= len(self.exp_rules):#if previous experiment was custom
            self.path_frame.pack_forget()
            self.update_idletasks()
            self.geometry(str(self.winfo_width()) + "x" + str(self.winfo_height()-80)+"+"+str(self.winfo_x())+"+"+str(self.winfo_y()-40))
            
        #get index of the selected experiment
        self.current_exp_index = self.exp_names.index(selected_exp)
        if self.current_exp_index < len(self.exp_rules):
            self.exp.from_dict(self.exp_rules[self.current_exp_index])
            self.update_treeview(self.exp.sequence)
        else:
            self.exp.from_json(self.path_entry.get())
            self.update_treeview(self.exp.sequence)

    def on_button_GO_click(self):
        # GO button logic
        self.add_log("Start experiment")
        #enable the pause and stop buttons
        self.command_PAUSE_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
        self.command_STOP_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
        self.command_GO_button.configure(state="disabled", fg_color="green")
        self.exp_combo.configure(state="disabled", fg_color="grey")
        self.path_entry.configure(state="disabled", fg_color="grey")
        self.path_browser_button.configure(state="disabled", fg_color="grey")
        self.exp.start()
    
    def on_button_PAUSE_click(self):
        # PAUSE button logic
        self.add_log("Pause experiment")
        self.exp.pause()
        self.command_PAUSE_button.configure(state="disabled", fg_color="yellow")
        self.command_STOP_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
        self.command_GO_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
        
    
    def on_button_STOP_click(self):
        # STOP button logic
        self.add_log("Stop experiment")
        self.exp.stop()
        if len(self.exp.sequence) > 0:
            self.exp_treeview.selection_set(self.exp_treeview.get_children()[0])
        self.command_PAUSE_button.configure(state="disabled", fg_color="grey")
        self.command_STOP_button.configure(state="disabled", fg_color="grey")
        self.command_GO_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
        self.exp_combo.configure(state="normal", fg_color="white")
        self.path_entry.configure(state="normal", fg_color="white")
        self.path_browser_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
    
    def on_add_comment_click(self):
        self.add_log("Comment: " + self.comments_entry.get())
        self.comments_entry.delete(0, tk.END)
        
    def add_log(self, text):
        self.log_text.insert(tk.END, time.strftime("%H:%M:%S") + "[" + str(time.time()) + "] - " + text + "\n")
        self.log_text.see(tk.END) 
        if self.file_log_open:
            self.file_log.write(time.strftime("%H:%M:%S") + "[" + str(time.time()) + "] - " + text + "\n")
            self.file_log.flush()
        
    def update_treeview(self, sequence):
        #delete all the items in the treeview
        self.exp_treeview.delete(*self.exp_treeview.get_children())
        #add the items
        for i in range(len(sequence)):
            self.exp_treeview.insert("", i, text=str(i), values=(sequence[i][1], round(sequence[i][2][1], 2)))
        #update the treeview
        self.exp_treeview.update_idletasks()
        if len(sequence) > 0:
            #set the selection to the first item
            self.exp_treeview.selection_set(self.exp_treeview.get_children()[0])
    
    def on_button_connect_click(self, event=None):
        # Connect button logic
        try:
            self.exp.connect_arduino(self.connection_entry.get())
            self.connection_button.configure(state="disabled", fg_color="grey")
            self.connection_entry.configure(state="disabled", fg_color="green")
            self.add_log("Connected to device: " + self.connection_entry.get())
            self.subject_entry.configure(state="normal", fg_color="white")
            self.validation_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
        except Exception as e:
            self.add_log("Error: " + str(e))
            #set the entry background to red
            self.connection_entry.configure(fg_color="red")
            
    def on_connection_entry_click(self, event):
        # Connect entry click logic
        self.connection_entry.configure(fg_color="white")
        
    def on_button_validate_user_click(self, event=None):
        # Validate user button logic
        if self.subject_entry.get() == "":
            self.add_log("Error: no subject name")
            self.subject_entry.configure(fg_color="red")
        else:
            self.add_log("User: " + self.subject_entry.get())
            self.subject_entry.configure(state="disabled", fg_color="green")
            self.validation_button.configure(state="disabled", fg_color="grey")
            #create log file
            filename = self.subject_entry.get() + "_" + time.strftime("%Y-%m-%d_%H-%M-%S") + ".log"
            self.file_log = open(filename, "w")
            #write evrything in the log text widget to the file
            self.file_log.write(self.log_text.get("1.0", tk.END))
            self.file_log_open = True
            self.command_GO_button.configure(state="normal", fg_color=['#3a7ebf', '#1f538d'])
            self.exp_combo.configure(state="normal", fg_color="white")
