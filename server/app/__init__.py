# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)

    socketio.init_app(app, cors_allowed_origins="*")

    from .utils import models, defines, calculateAB, gui, initialize_directories
    from .process import process_chat, process_speed, process_character_data, process_events, process_map
    from .comm import comm_map_data, comm

    # Register your blueprints or other components here

    return app
