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
from . import config

def initialize_directories():

    if config.main_directory_path:
        # Simply define the paths without creating directories or files
        config.info_path = os.path.join(config.main_directory_path, 'Plugins', 'info')
        config.count_path = os.path.join(config.info_path, 'messages', 'count.json')
        config.config_path = os.path.join(config.main_directory_path, 'Config')
        config.statz_path = os.path.join(config.info_path, 'statz')
        config.chat_path = os.path.join(config.info_path, 'messages', 'msgs')
        config.stall_path = os.path.join(config.info_path, 'stall')
        config.events_path = os.path.join(config.info_path, 'events')

        # Only create these directories if they don't exist
        config.live_chat_path = os.path.join(config.info_path, 'messages', 'LIVE')
        config.tasks_path = os.path.join(config.info_path, 'tasks')
        config.speed_path = os.path.join(config.tasks_path, 'speed')

        directories_to_create = [config.live_chat_path, config.tasks_path, config.speed_path]

        for directory in directories_to_create:
            os.makedirs(directory, exist_ok=True)

