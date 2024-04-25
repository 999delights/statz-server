import os
from datetime import datetime

import json
from .. import socketio
from ..utils import var




@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


#@socketio.on('disconnect_request')
#def disconnect_request():
#    disconnect()



@socketio.on('new_CHAT')  # Create a new event 'new_MESSAGES'
def handle_new_messages():
    try:
        # Specify the path to the count.json file
        save_path = r'C:\Users\andre\AppData\Local\Programs\phBot Testing\Plugins\info\messages\count.json'

        # Check if the file exists and remove it if it does
        if os.path.exists(save_path):
            os.remove(save_path)

        # Emit a signal to indicate that the file has been removed
        socketio.emit('count_file_removed')

    except Exception as e:
        # Handle any exceptions that may occur while removing the file
        socketio.emit('count_file_remove_error', str(e))











@socketio.on('speed_cast')
def handle_speed_cast(payload):
   
    var.speed_pause = True
    # Extract details from payload
    character_name = payload['character']
    server_name = payload['server']
    checked_value = payload['checked']
    players_list = payload['list']
    isBard = payload['isBard']
    main = payload['main']
    job_mode = payload['jobMode']
    # Formulate the data to save
    data_dict = { 
        f"{character_name}/{server_name}": {  # Maintain the '/' in the key for readability
            "checked": checked_value,
            "list": players_list,
            "isBard": isBard,
            'main': main,
            
            'jobMode':job_mode
     
        }
    }


    # Complete file path
    file_path = os.path.join(var.speed_path, server_name, f'{character_name}.json')
    
    # Verify directory exists or create it (for nested character/server structures)
    dir_path = os.path.dirname(file_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Save the data to the JSON file
    try:
        with open(file_path, 'w') as file:
            json.dump(data_dict, file)
        print(f"Data for {character_name} on {server_name} saved successfully.")
    except Exception as e:
        print(f"Failed to save data for {character_name} on {server_name}. Error: {e}")

    var.speed_pause = False




###########################################
###########################################
########## DATA FROM INFO FOLDER ##########
###########################################
#LIVE-ALL SENT MESSAGES FROM APP(CLIENT)


@socketio.on('live_chat')
def handle_message(data):
    if data:
        try:
            # Extract sender's name from the message data
            sender = data['from']
            server = data['server']
            # Generate a filename based on the current date and time
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Create a directory for the sender under "messages" if it doesn't exist
            sender_dir = os.path.join(var.live_chat_path, server, sender)
            if not os.path.exists(sender_dir):
                os.makedirs(sender_dir)

            # Path to save the JSON file
            filename = os.path.join(sender_dir, f'{current_date}.json')

            # Save the message data as a JSON file
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)

        except Exception as e:
            # If you're using some logging mechanism, you can log the error here
            pass