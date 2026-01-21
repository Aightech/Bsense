import ui.main_window
import sys
import logging

if __name__ == "__main__":
    debug = False
    port = None  # Will use platform default if not specified
    file = ""

    # Parse command line arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-d":
            debug = True
        elif args[i] == "-p" and i + 1 < len(args):
            port = args[i + 1]
            i += 1
        elif args[i] == "-f" and i + 1 < len(args):
            file = args[i + 1]
            i += 1
        i += 1

    # Configure logging based on debug mode
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    gui = ui.main_window.BsenseGUI()
    if debug:
        gui.debug_mode()
    if port:
        gui.set_port(port)
    if file:
        gui.set_file(file)
    gui.run()
