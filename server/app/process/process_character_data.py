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
import json
import time
from ..utils import config



###########################################
#GET THE STATZ FROM INFO FOLDER  (PLUGIN)
#THIS INCLUDE THE STALL DATA TOO IN THE SAME JSON
def process_character_data():
    

    # Initialize local dictionaries for compiling data
    local_data = {}
    local_stall_data = {}

    # Helper function to read JSON with retries
    def read_json_with_retries(file_path, max_retries=16):
        for attempt in range(max_retries):
            try:
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    return json.load(json_file)
            except json.JSONDecodeError:
                print(f"Attempt {attempt + 1} failed to decode JSON in {file_path}")
                if attempt == max_retries - 1:  # Last attempt also failed
                    print(f"Final attempt to read {file_path} failed.")
                    return None  # or {} if you prefer to return an empty dict instead of None
        return None

    # Process the 'statz' directory for statistical data
    for directory in os.listdir(config.statz_path):
        directory_path = os.path.join(config.statz_path, directory)
        if os.path.isdir(directory_path):  # Ensure it's a directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):  # Focus on JSON files
                    file_path = os.path.join(directory_path, filename)
                    data = read_json_with_retries(file_path)
                    if data is not None:
                        for key, value in data.items():
                            if key in local_data:  # Merge data into local_data
                                local_data[key].update(value)
                            else:
                                local_data[key] = value

    # Process the 'stall' directory for stall-related activities
    for directory in os.listdir(config.stall_path):
        directory_path = os.path.join(config.stall_path, directory)
        if os.path.isdir(directory_path):  # Ensure it's a directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):  # Focus on JSON files
                    file_path = os.path.join(directory_path, filename)
                    data = read_json_with_retries(file_path)
                    if data is not None:
                        for key, value in data.items():
                            if key in local_stall_data:  # Merge data into local_stall_data
                                local_stall_data[key].update(value)
                            else:
                                local_stall_data[key] = value

    # Merge local_stall_data into local_data
    for key, value in local_stall_data.items():
        if key in local_data:
            local_data[key].update(value)

     # Update the global statz_data with the compiled local_data
    for key, value in local_data.items():
        if key in config.statz_data:
            # If the key exists in statz_data, update it
            config.statz_data[key].update(value)
        else:
            # If the key doesn't exist, add it to statz_data
            config.statz_data[key] = value