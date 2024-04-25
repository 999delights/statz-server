import os
from threading import Thread, Event
import tkinter as tk
from tkinter import filedialog
import eventlet
eventlet.monkey_patch()
from turtle import speed
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
import json
import time
from ..utils import var
from datetime import datetime, timedelta

# Function to parse datetime from filename


def parse_datetime_from_filename(filename):
    # Remove the .json extension if present
    filename = filename.replace('.json', '')
    
    # Split at the underscore to separate date and time
    date_str, time_str = filename.split('_')

    # Parse the date part
    year, month, day = map(int, date_str.split('-'))

    # Remove potential file extension and parse the time part
    hour, minute, second = map(int, time_str.split('-'))

    # Return the datetime object
    return datetime(year, month, day, hour, minute, second)

def calculate_threshold_date():
    THRESHOLD_DAYS = 14
    return datetime.now() - timedelta(days=THRESHOLD_DAYS)

def process_events():
    threshold_date = calculate_threshold_date()
    files_to_delete = []

    for server in os.listdir(var.events_path):
        server_dir = os.path.join(var.events_path, server)
        for character in os.listdir(server_dir):
            character_dir = os.path.join(server_dir, character)
            event_files = sorted(os.listdir(character_dir))
            for file_name in event_files:
                file_path = os.path.join(character_dir, file_name)
                file_datetime = parse_datetime_from_filename(file_name)

                # Process the file based on its date
                if file_datetime < threshold_date:
                    # Add older files to the deletion list
                    files_to_delete.append(file_path)
                else:
                    # Load and process events for files within the threshold
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            data = json.load(file)
                            for event_key, event_data in data.items():
                                var.events_data.setdefault(event_key, []).append(event_data)
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")

    # Delete files marked for deletion
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except FileNotFoundError:
            print(f"File already deleted: {file_path}")

    print("Event processing complete.")

    # Save the extracted data to events.json once after processing all events
    output_file_path = os.path.join(var.info_path, 'events.json')  # Ensure info_path is correctly defined
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(var.events_data, output_file, indent=4)
    print("Events data saved.")
