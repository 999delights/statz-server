import os
from datetime import datetime
from turtle import speed
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
import json
import time
import eventlet
import logging
eventlet.monkey_patch()


app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=5, ping_interval=2, cors_allowed_origins="*")













# Define the main directory path where the phBot plugins store their data.
main_directory_path = r'C:\Users\andre\AppData\Local\Programs\phBot Testing\Plugins\info'

count_path = r'C:\Users\andre\AppData\Local\Programs\phBot Testing\Plugins\info\messages\count.json'


# Define paths for additional directories within the main directory to organize data more specifically.

#DIRECTORIES WITH DATA FROM PLUGINS
statz_directory = os.path.join(main_directory_path, 'statz')
msgs_directory = os.path.join(main_directory_path, 'messages', 'msgs')
stall_directory = os.path.join(main_directory_path, 'stall')
events_directory = os.path.join(main_directory_path, 'events')


# Initialize empty dictionaries to temporarily store the gathered data before sending.
statz_data = {}
messages_data = {}
events_data = {}
manager_data = {}
new_messages_saved = False


#DIRECTORIES WITH DATA FROM CLIENT
# Verify if the "LIVE messages" directory exists or create it
messages_dir = os.path.join(main_directory_path, 'messages/LIVE')
if not os.path.exists(messages_dir):
    os.makedirs(messages_dir)

# Verify if the "tasks" directory exists or create it
tasks_dir = os.path.join(main_directory_path, 'tasks')
if not os.path.exists(tasks_dir):
    os.makedirs(tasks_dir)

# Verify if the "speed" directory exists or create it
speed_dir = os.path.join(tasks_dir, 'speed')
if not os.path.exists(tasks_dir):
    os.makedirs(tasks_dir)




###########################################
###########################################
########## DATA FROM INFO FOLDER ##########

def process_events(main_dir):    
    for server in os.listdir(main_dir):
        server_dir = os.path.join(main_dir, server)
        if os.path.isdir(server_dir):
            for character in os.listdir(server_dir):
                character_dir = os.path.join(server_dir, character)
                if os.path.isdir(character_dir):
                    event_files = sorted(os.listdir(character_dir))
                    for file_name in event_files:
                        file_path = os.path.join(character_dir, file_name)
                        # Check if file exists before attempting to open
                        if not os.path.exists(file_path):
                            print(f"File not found: {file_path}")
                            continue
                        try:
                            with open(file_path, 'r') as f:
                                data = json.load(f)
                        except json.JSONDecodeError as e:
                            print(f"Error reading file {file_path}: {e}")
                            continue
                        key = next(iter(data))
                        event_name = data[key]['event_name']
                        
                        # Append data to the master JSON
                        events_data.setdefault(key, []).append(data[key])

                        # For "EVENT_CONNECTED" events, look for corresponding "EVENT_DISCONNECTED"
                        if event_name == "EVENT_CONNECTED":
                            connected_date = datetime.strptime(file_name.split('.')[0], "%Y-%m-%d_%H-%M-%S")
                            disconnect_found = False
                            for check_file in event_files:
                                if check_file > file_name: # Look for files with a later date
                                    check_path = os.path.join(character_dir, check_file)
                                    with open(check_path, 'r') as f:
                                        check_data = json.load(f)
                                    check_key = next(iter(check_data))
                                    if check_data[check_key]['event_name'] == "EVENT_DISCONNECTED":
                                        disconnect_found = True
                                        # Append EVENT_DISCONNECTED to master and delete both files
                                        events_data.setdefault(check_key, []).append(check_data[check_key])
                                        os.remove(check_path)  # Delete EVENT_DISCONNECTED file
                                        break
                            if disconnect_found:
                                # Before deleting, check if the file exists
                                if os.path.exists(file_path):
                                    os.remove(file_path)  # Delete EVENT_CONNECTED file only if disconnect is found
                                else:
                                    print(f"File not found, cannot delete: {file_path}")
                        else:
                            # Delete files for events other than "EVENT_CONNECTED" after appending
                            os.remove(file_path)

###########################################
#GET THE STATZ FROM INFO FOLDER  (PLUGIN)
#THIS INCLUDE THE STALL DATA TOO IN THE SAME JSON
def processData():
    global statz_data  # Reference the global variable to update it later

    # Initialize local dictionaries for compiling data
    local_data = {}
    local_stall_data = {}

    # Process the 'statz' directory for statistical data
    for directory in os.listdir(statz_directory):
        directory_path = os.path.join(statz_directory, directory)
        if os.path.isdir(directory_path):  # Ensure it's a directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):  # Focus on JSON files
                    file_path = os.path.join(directory_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        try:
                            data = json.load(json_file)
                            for key, value in data.items():
                                if key in local_data:  # Merge data into local_data
                                    local_data[key].update(value)
                                else:
                                    local_data[key] = value
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON in {filename}")

    # Process the 'stall' directory for stall-related activities
    for directory in os.listdir(stall_directory):
        directory_path = os.path.join(stall_directory, directory)
        if os.path.isdir(directory_path):  # Ensure it's a directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):  # Focus on JSON files
                    file_path = os.path.join(directory_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        try:
                            data = json.load(json_file)
                            for key, value in data.items():
                                if key in local_stall_data:  # Merge data into local_stall_data
                                    local_stall_data[key].update(value)
                                else:
                                    local_stall_data[key] = value
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON in {filename}")

    # Merge local_stall_data into local_data
    for key, value in local_stall_data.items():
        if key in local_data:
            local_data[key].update(value)
        else:
            local_data[key] = value

    # Finally, replace the global helper_data with the compiled local_data
    statz_data = local_data
########################################### 
    

###########################################
#GET THE MESSAGES FROM INFO FOLDER  (PLUGIN)
#THIS INCLUDE THE COUNT LOGIC 
def processMessages():
    global messages_data
    global new_messages_saved
    # Initialize local dictionaries for compiling data
    local_messages_data = {}
    local_count = {}  # Local dictionary for message counts

    # Process the 'messages' directory: gather chat and message data.
    for directory in os.listdir(msgs_directory):
        directory_path = os.path.join(msgs_directory, directory)
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

                    # Optionally, clear contents of specific files to avoid data duplication
                    if filename.startswith('message_'):
                        with open(file_path, 'w', encoding='utf-8') as file_to_clear:
                            file_to_clear.write('')

    # After processing, update the global messages_data
    messages_data = local_messages_data

    # Compile message counts from local_messages_data into local_count
    for character, character_data in local_messages_data.items():
        msgs_count = len(character_data.get('msgs', []))
        dmTOmsgs_count = len(character_data.get('dmTOmsgs', []))
        local_count[character] = {'msgs': msgs_count, 'dmTOmsgs': dmTOmsgs_count}

    # Check the existence of the count.json file and compare with local_count
    if not os.path.exists(count_path):
        new_messages_saved = True  # File doesn't exist, new data available
        # Create the file and write local_count data
        with open(count_path, 'w', encoding='utf-8') as json_file:
            json.dump(local_count, json_file, indent=4)
    else:
        # Load existing data and compare with local_count
        with open(count_path, 'r', encoding='utf-8') as json_file:
            existing_count_data = json.load(json_file)
        # Compare existing data with local_count
        if existing_count_data != local_count:
            new_messages_saved = True  # Data differs, new data available
            # Update the file with new local_count data
            with open(count_path, 'w', encoding='utf-8') as json_file:
                json.dump(local_count, json_file, indent=4)
    
###########################################



########## DATA FROM INFO FOLDER ##########
###########################################
###########################################







###########################################
###########################################
############## FROM HELPER ################
    







# GET THE STATS SENT FROM PHBOT URL SYSTEM (MANAGER) 
############################################
@app.route('/phBotHTTP', methods=['POST'])
def phBotHTTP():
    global manager_data
    data = request.form.get('data')
    if data:
        # Replace "1.#INF" with null in the data string
        cleaned_data = data.replace("1.#INF", "null")

        # Load the modified JSON data as a dictionary
        data_dict = json.loads(cleaned_data)

        # Remove the 'time_to_level' field from each sub-dictionary
        for key in data_dict:
            if 'time_to_level' in data_dict[key]:
                del data_dict[key]['time_to_level']

        # Set the modified dictionary as the latest_data
        manager_data = data_dict

        return "Data received and stored for process1"
    else:
        return "No data received"
############################################ 



############## FROM HELPER ################
###########################################
###########################################





###########################################
###########################################
############## FROM CLIENT ################



###########################################
#LIVE-ALL SENT MESSAGES FROM APP(CLIENT)
@socketio.on('messages')
def handle_message(data):
    if data:
        try:
            # Extract sender's name from the message data
            sender = data['from']
            server = data['server']
            # Generate a filename based on the current date and time
            current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # Create a directory for the sender under "messages" if it doesn't exist
            sender_dir = os.path.join(messages_dir, server, sender)
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
###########################################



############## FROM CLIENT ################
###########################################
###########################################





###########################################
###########################################
############## TO CLIENT ##################



###########################################
# SEND STATZ (FROM PLUGIN + MANAGER) TO CLIENT
# NEED TO MERGE THOSE 2 DATA JSON INTO SAME KEY (CHARACTER/SERVER)
###########################################
socketio.on('fetch_STATZ')
def handle_fetch_characters():
    if manager_data and statz_data:
        for key_data in manager_data.copy():
            # Get the character name
            name_data = key_data.split('/')[-1]
            
            # Get the server info from latest_data
            server_info = manager_data[key_data]['server']
            
            # Append server info to name_data
            name_data = f"{name_data}/{server_info}"
            
            for key_info in statz_data:
                if name_data == key_info:
                    manager_data[key_data].update(statz_data[key_info])
                    
        # Emit socket after all character data has been checked
        socketio.emit('characters_data', manager_data)
    else:
        socketio.emit('characters_error', 'No data available yet.')
###########################################


###########################################
# SEND MESSAGES (WHEN new_messages_saved is True) TO CLIENT
###########################################
socketio.on('fetch_MESSAGES')
def handle_fetch_messages():
    global new_messages_saved
    if new_messages_saved:
        socketio.emit('characters_messages', messages_data)  # Emit latest_messages to the client
        new_messages_saved = False  # Reset new_messages_saved to False
    else:
        socketio.emit('characters_error', 'No new messages available yet.')
###########################################



############## TO CLIENT ##################
###########################################
###########################################



def background_task():
    """Background task to send socketio messages."""
    while True:
        processData()
        processMessages()
        handle_fetch_characters()
        handle_fetch_messages() 
        process_events(events_directory)
        time.sleep(2)  


socketio.start_background_task(background_task)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 




@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('disconnect_request')
def disconnect_request():
    disconnect()




@socketio.on('new_MESSAGES')  # Create a new event 'new_MESSAGES'
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





       
# @app.route('/sendTasks', methods=['POST'])
# def savTasks():
#     data = request.get_json()
#     if data:
#         try:
#             # Extract sender's name from the message data
#             sender = data['from']
            
#             # Generate a filename based on the current date and time
#             current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#             # Create a directory for the sender under "messages" if it doesn't exist
#             sender_dir = os.path.join(tasks_dir, sender)
#             if not os.path.exists(sender_dir):
#                 os.makedirs(sender_dir)

#             # Path to save the JSON file
#             filename = os.path.join(sender_dir, f'{current_date}.json')

#             # Save the message data as a JSON file
#             with open(filename, 'w') as file:
#                 json.dump(data, file, indent=4)

#             return "Message saved successfully"
#         except Exception as e:
#             return f"Error saving message: {str(e)}"
#     else:
#         return "No message received"





 # OLD URL SYSTEM TO SEND STATS   
@app.route('/characters', methods=['GET'])
def get_characters():
    if statz_data:
        # if latest_info:
            
        #     # Iterate through keys in latest_data
        #     for key_data in latest_data.copy():
        #         # Extract the NAME from the key in latest_data
        #             name_data = key_data.split('/')[-1]

        #             # Iterate through keys in latest_info
        #             for key_info in latest_info:
        #                 # Check if the NAME from latest_info matches the extracted NAME from latest_data
        #                 if name_data == key_info:
        #                     # Append data from latest_info to latest_data under the key in latest_data
        #                     latest_data[key_data].update(latest_info[key_info])
        
        return manager_data  # Return the dictionary as JSON
      
        
    else:
        return "No data available yet.", 404  



# @socketio.on('speed_cast')
# def handle_speed_cast(payload):
    
#     # Extract the character name and other necessary details
#     character_name = payload['character']
#     checked_value = payload['checked']
#     players_list = payload['players']
#     isBard = payload['isBard']
#     # Formulate the dictionary to be saved
#     data_dict = {
       
#             "checked": checked_value,
#             "players": players_list,
#             "isBard": isBard
        
#     }
    
#     # Define the file path for the JSON file
#     file_path = os.path.join(speed_dir, f"{character_name}.json")
    
#     # Save the data to the JSON file
#     with open(file_path, 'w') as file:
#         json.dump(data_dict, file)


