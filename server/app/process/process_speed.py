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
from ..utils import var





###########################################
#GET THE SPEED FROM INFO FOLDER  (PLUGIN)
def process_speed():


    # Initialize local dictionaries for compiling data
    local_data = {}
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
    if var.speed_pause == False:
        var.speed_data = {}
       
        for directory in os.listdir(var.speed_path):
            directory_path = os.path.join(var.speed_path, directory)
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


        # Update the global statz_data with the compiled local_data
        for key, value in local_data.items():
            if key in var.speed_data:
                # If the key exists in statz_data, update it
                var.speed_data[key].update(value)
            else:
                # If the key doesn't exist, add it to statz_data
                var.speed_data[key] = value
        output_file_path = os.path.join(var.info_path, 'speed.json')
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(var.speed_data, output_file, indent=4)
