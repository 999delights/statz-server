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
#GET THE MESSAGES FROM INFO FOLDER  (PLUGIN)
#THIS INCLUDE THE COUNT LOGIC 
def process_chat():

    # Initialize local dictionaries for compiling data
    local_messages_data = {}
    local_count = {}  # Local dictionary for message counts

    # Process the 'messages' directory: gather chat and message data.
    for directory in os.listdir(var.chat_path):
        directory_path = os.path.join(var.chat_path, directory)
        if os.path.isdir(directory_path):  # Check if the item is a directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):  # Process only JSON files
                    file_path = os.path.join(directory_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as json_file:  # Open and read the JSON file
                        try:
                            data = json.load(json_file)  # Load the JSON data into a dictionary
                            for key, value in data.items():
                                if key in local_messages_data:  # Merge data into local_messages_data
                                    local_messages_data[key].update(value)
                                else:  # If the key is new, add it to the local_messages_data dictionary
                                    local_messages_data[key] = value
                        except json.JSONDecodeError:  # Handle possible JSON decoding errors
                            print(f"Error decoding JSON in {filename}")


    # After processing, update the global messages_data
    var.chat_data = local_messages_data

    # Compile message counts from local_messages_data into local_count
    for character, character_data in local_messages_data.items():
        msgs_count = len(character_data.get('msgs', []))
        dmTOmsgs_count = len(character_data.get('dmTOmsgs', []))
        local_count[character] = {'msgs': msgs_count, 'dmTOmsgs': dmTOmsgs_count}

    # Check the existence of the count.json file and compare with local_count
    if not os.path.exists(var.count_path):
        var.new_chat_saved = True  # File doesn't exist, new data available
        # Create the file and write local_count data
        with open(var.count_path, 'w', encoding='utf-8') as json_file:
            json.dump(local_count, json_file, indent=4)
    else:
        # Load existing data and compare with local_count
        with open(var.count_path, 'r', encoding='utf-8') as json_file:
            existing_count_data = json.load(json_file)
        # Compare existing data with local_count
        if existing_count_data != local_count:
            var.new_chat_saved = True  # Data differs, new data available
            # Update the file with new local_count data
            with open(var.count_path, 'w', encoding='utf-8') as json_file:
                json.dump(local_count, json_file, indent=4)
    