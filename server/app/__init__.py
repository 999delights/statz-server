from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=5, ping_interval=2, cors_allowed_origins="*")

# Make sure that no other imports happen until after the above definitions
