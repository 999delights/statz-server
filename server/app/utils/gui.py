
import os
from threading import Thread, Event
import tkinter as tk
from tkinter import filedialog
import eventlet
eventlet.monkey_patch()
from datetime import datetime
from turtle import speed
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
from . import config


    

def start_gui(gui_done):
    

    def select_path(var_name):
        path = filedialog.askdirectory() if var_name == "main_directory_path" else filedialog.askopenfilename()
        if path:
            # Set the attribute on config when a path is chosen
            setattr(config, var_name, path)
            print(f"{var_name} set to: {getattr(config, var_name)}")  # Display the path for debugging
            
            # Check if all required paths are set before enabling the server start button
            if all([config.main_directory_path, config.manager_exe_path, config.silkroad_launcher_path]):
                print("All required paths have been selected. Enabling server start.")
                start_server_button['state'] = 'normal'
            else:
                print("Please select all required paths.")
            labels[var_name].config(text=path)  # Update the label with the selected path

    window = tk.Tk()
    window.title("Select Required Paths")
    # Maximize the window
    window.state('zoomed')

    # Using a frame to easily center widgets
    center_frame = tk.Frame(window)
    center_frame.pack(expand=True)

    labels = { 
        "main_directory_path": tk.Label(center_frame, text="No directory selected"),
        "manager_exe_path": tk.Label(center_frame, text="No file selected"),
        "silkroad_launcher_path": tk.Label(center_frame, text="No file selected")
    }

    # Adjusting the grid and adding more space between buttons and labels
    tk.Button(center_frame, text="Browse phBot Directory", command=lambda: select_path("main_directory_path")).grid(row=0, column=0, pady=(10, 2), padx=10)
    labels["main_directory_path"].grid(row=1, column=0, pady=(2, 10), padx=10)
    tk.Button(center_frame, text="Browse Manager.exe", command=lambda: select_path("manager_exe_path")).grid(row=2, column=0, pady=(10, 2), padx=10)
    labels["manager_exe_path"].grid(row=3, column=0, pady=(2, 10), padx=10)
    tk.Button(center_frame, text="Browse Silkroad Launcher", command=lambda: select_path("silkroad_launcher_path")).grid(row=4, column=0, pady=(10, 2), padx=10)
    labels["silkroad_launcher_path"].grid(row=5, column=0, pady=(2, 10), padx=10)
    print("from start_gui: Waiting for gui_done event.")
    start_server_button = tk.Button(center_frame, text="Start Server", state='disabled', 
                                command=lambda: (gui_done.set(), window.destroy()))

    start_server_button.grid(row=6, column=0, pady=20, padx=10)

    window.mainloop()