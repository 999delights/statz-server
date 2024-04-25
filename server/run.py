import os
from threading import Thread, Event
import tkinter as tk
from tkinter import filedialog
import eventlet
eventlet.monkey_patch()
from datetime import datetime
from turtle import speed

import json
import time
from app.utils.initialize_directories import initialize_directories
from app.process.process_speed import process_speed
from app.process.process_character_data import process_character_data
from app.process.process_chat import  process_chat
from app.process.process_events import  process_events
#from app.process.process_map import process_map
from app.comm.comm_raw_data import handle_fetch_characters
from app.comm.comm_raw_data import handle_fetch_events
from app.comm.comm_raw_data import handle_fetch_speed
from app.comm.comm_raw_data import handle_fetch_chat
from app.utils import var
from app.utils.gui import start_gui
from app import create_app, socketio

app = create_app()

def background_task():
    """Background task to send socketio messages."""
    while True:
        process_character_data()
        process_chat()
        process_speed()
        

        #extract_conditions_data()  # config

        handle_fetch_characters()
        handle_fetch_chat() 
        handle_fetch_events()
        handle_fetch_speed()
        process_events()
        time.sleep(3)  


def start_server():
    print("from start_server: Waiting for gui_done event.")
    gui_done.wait()  # Wait for the GUI to finish initializing
    print(f"Paths at server start: Main={var.main_directory_path}, Manager={var.manager_exe_path}, Launcher={var.silkroad_launcher_path}")
    
    if all([var.main_directory_path, var.manager_exe_path, var.silkroad_launcher_path]):
        print("All necessary paths have been selected.")
        initialize_directories()
        socketio.start_background_task(background_task)
        print("Server starting...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    else:
        print("One or more required paths are not set. Server not started.")


if __name__ == '__main__':
    
    gui_done = Event()
    # Run GUI in the main thread
    start_gui(gui_done)  # Pass the Event to the GUI function
    # Start the server in the main thread after GUI has finished
    print("Paths at server start:", var.main_directory_path, var.manager_exe_path, var.silkroad_launcher_path)

    start_server()