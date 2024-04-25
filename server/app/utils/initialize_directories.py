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
from . import var

def initialize_directories():

    if var.main_directory_path:
        # Simply define the paths without creating directories or files
        var.info_path = os.path.join(var.main_directory_path, 'Plugins', 'info')
        var.count_path = os.path.join(var.info_path, 'messages', 'count.json')
        var.config_path = os.path.join(var.main_directory_path, 'config')
        var.statz_path = os.path.join(var.info_path, 'statz')
        var.chat_path = os.path.join(var.info_path, 'messages', 'msgs')
        var.stall_path = os.path.join(var.info_path, 'stall')
        var.events_path = os.path.join(var.info_path, 'events')

        # Only create these directories if they don't exist
        var.live_chat_path = os.path.join(var.info_path, 'messages', 'LIVE')
        var.tasks_path = os.path.join(var.info_path, 'tasks')
        var.speed_path = os.path.join(var.tasks_path, 'speed')

        directories_to_create = [var.live_chat_path, var.tasks_path, var.speed_path]

        for directory in directories_to_create:
            os.makedirs(directory, exist_ok=True)

