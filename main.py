import ui.main_window
import sys

if __name__ == "__main__":
    debug = False
    port = "COM3"
    file = ""
    #check if -d flag is present for debug mode
    for arg in sys.argv:
        if arg == "-d":
            debug = True
        if arg == "-p":
            print("serial port")
            port = sys.argv[sys.argv.index(arg)+1]
        if arg == "-f":
            print("file")
            file = sys.argv[sys.argv.index(arg)+1]

    gui = ui.main_window.BsenseGUI()
    if debug:
        gui.debug_mode()
    gui.set_port(port)
    if file != "":
        gui.set_file(file)
    gui.run()
