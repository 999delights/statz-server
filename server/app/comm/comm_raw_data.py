
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
from .. import app, socketio
from ..utils import config




socketio.on('fetch_STATZ')
def handle_fetch_characters():
   

    local_statz_data = config.statz_data.copy()  # Create a local copy of statz_data
    info_data = {}  # Initialize a local dictionary for the merged data

    # Copy only keys from statz_data to info_data where the manager data is true
    for key, value in local_statz_data.items():
        if value.get('manager') == True:  # Check if the manager data is true
            info_data[key] = value

    # Check if there is any data to emit
    if info_data:
        # Emit the filtered data via socket
        socketio.emit('characters_data', info_data)
    else:
        # Emit an error message if no data available that meets the criteria
        socketio.emit('characters_error', 'No data available yet or manager data not set to true.')

socketio.on('fetch_EVENTS')
def handle_fetch_events():

   

    if config.events_sent == False:
                # Emit the events data via socket
        socketio.emit('characters_events', config.events_data)
        config.events_sent = True

    else:
        # Emit an error message if no data is available
        socketio.emit('events_error', 'No data available yet.')





socketio.on('fetch_CHAT')
def handle_fetch_chat():
    if config.new_chat_saved:
        socketio.emit('characters_chat', config.chat_data)  # Emit latest_messages to the client
        config.new_chat_saved = False  # Reset new_messages_saved to False
    else:
        socketio.emit('characters_error', 'No new messages available yet.')

socketio.on('fetch_SPEED')
def handle_fetch_speed():

    

    if not config.speed_pause and config.speed_data:
                # Emit the events data via socket
        socketio.emit('characters_speed', config.speed_data)
    else:
        # Emit an error message if no data is available
        socketio.emit('speed_error', 'No data available yet.')

