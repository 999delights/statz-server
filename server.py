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
import re

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
if not os.path.exists(speed_dir):
    os.makedirs(speed_dir)


#CONFIG DIR
config_directory_path = r'C:\Users\andre\AppData\Local\Programs\phBot Testing\Config'









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
    global manager_data  # Although not directly modified, declared for clarity
    global statz_data  # Same as above

    # Create local copies of the global data
    local_manager_data = manager_data
    local_statz_data = statz_data
    info_data = {}  # Initialize a local dictionary for the merged data

    # Merge logic
    for key_data in local_manager_data:
        # Get the character name
        name_data = key_data.split('/')[-1]

        # Get the server info from manager data
        server_info = local_manager_data[key_data]['server']

        # Append server info to name_data to match the key format in statz_data
        merged_key = f"{name_data}/{server_info}"

        # Check if the merged key exists in statz_data
        if merged_key in local_statz_data:
            # If so, merge statz_data under the key into the manager data for the corresponding character
            local_manager_data[key_data].update(local_statz_data[merged_key])

            # Additionally, update or create the entry in info_data with the merged data
            info_data[key_data] = local_manager_data[key_data]

    # Check if there is any data to emit
    if info_data:
        # Emit the combined data via socket
        socketio.emit('characters_data', info_data)
    else:
        # Emit an error message if no data is available
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


@socketio.on('speed_cast')
def handle_speed_cast(payload):
    # Extract details from payload
    character_name = payload['character']
    server_name = payload['server']
    checked_value = payload['checked']
    players_list = payload['list']
    isBard = payload['isBard']
    main = payload['main']
    march = payload['march']
  
    # Formulate the data to save
    data_dict = { 
        f"{character_name}/{server_name}": {  # Maintain the '/' in the key for readability
            "checked": checked_value,
            "list": players_list,
            "isBard": isBard,
            'main': main,
            'march':march,
     
        }
    }


    # Complete file path
    file_path = os.path.join(speed_dir, server_name, f'{character_name}.json')
    
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



###########################################
###########################################
######### DATA FROM CONFIG FOLDER #########


def extract_conditions_data():
   

    # Create a dictionary to store conditions data for each file
    conditions_data = {}

    # Define a regular expression pattern to match the filename pattern "server_character.json"
    filename_pattern = re.compile(r'^(.+)_(.+)\.json$')

    # Iterate over files in the config directory
    for file_name in os.listdir(config_directory_path):
        if file_name.endswith('.json'):
            # Check if the filename matches the pattern
            match = filename_pattern.match(file_name)
            if match:
                server = match.group(1)
                character = match.group(2)





                file_path = os.path.join(config_directory_path, file_name)
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    try:
                        data = json.load(json_file)
                        conditions_data[f"{server}_{character}"] = data.get('Conditions', {})
                    except (json.JSONDecodeError, ValueError):
                        print(f"Error processing file {file_path}")
          

    # Save the extracted data to conditions.json in main_directory_path
    output_file_path = os.path.join(main_directory_path, 'conditions.json')
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(conditions_data, output_file, indent=4)

######### DATA FROM CONFIG FOLDER #########
###########################################
###########################################







def speed_condition():

    # Define a regular expression pattern to match the filename pattern "server_character.json"
    filename_pattern = re.compile(r'^(.+)_(.+)\.json$')



        # Iterate through each server folder
    for server_name in os.listdir(speed_dir):
        server_path = os.path.join(speed_dir, server_name)
        if os.path.isdir(server_path):
            # Iterate through each character JSON file in the server directory
            for file_name in os.listdir(server_path):
                if file_name.endswith('.json') and not file_name.startswith('condition'):
                    character_path = os.path.join(server_path, file_name)
                    with open(character_path, 'r') as json_file:
                        character_data = json.load(json_file)
                        for key, values in character_data.items():
                            character_name, character_server = key.split('/')
                            
                            checked = values.get('checked', False)
                            item_list = values.get('list', [])
                            march = values.get('march',"")
                            is_bard = values.get('isBard', False)
                            main = values.get('main', "")
                            # Save to a new file in the same server directory
                            export_filename = f"condition_{character_name}.json"
                            export_path = os.path.join(server_path, export_filename)
                            # If checked is true, is bard, and main is true
                            if checked:
                                if is_bard:
                                    base_conditions = [
                                        {"if": 10, "op": 2, "value_1": "checkrecastspeed", "value_2": ""},
                                        {"if": 11, "op": 2, "value_1": "", "value_2": ""}
                                    ]

                                    # Initialize then_clause based on 'main'
                                    if main == "Main":
                                        then_clause = [
                                            {"then": 49, "value": "ok", "value_2": ""},
                                            {"then": 15, "value": march, "value_2": ""}
                                        ]
                                        # Define export_data with the appropriate configuration
                                        export_data = {
                                            f"{character_server}_{character_name}": [{
                                                "Enabled": True,
                                                "if": base_conditions,
                                                "then": then_clause,
                                               
                                            }]
                                        }
                                    else:
                                        for name in item_list:
                                            base_conditions.append({"if": 1, "op": 2, "value_1": name, "value_2": ""})         #if main not in training area

                                        if march == "Swing March":


                                            then_clause =  [{"then": 49, "value": "ok", "value_2": ""},                     # ok message

                                                            {"then": 17, "value": "cast_Swing", "value_2": ""}]               # cast speed if not main    SWING  
                                        else:
                                            then_clause =  [{"then": 49, "value": "ok", "value_2": ""},                     # ok message

                                                            {"then": 17, "value": "cast_Moving", "value_2": ""}] 
                                                          # cast speed if not main    
                                        # Append a new configuration for the current item
                                        export_data = {
                                            f"{character_server}_{character_name}": [{
                                                "Enabled": True,
                                                "if": base_conditions,
                                                "then": then_clause,
                                               
                                            }]
                                        }

                                if not is_bard:
                                    base_conditions = [
                                        {"if": 11, "op": 2, "value_1": "", "value_2": ""},
                                        {"if": 19, "op": 2, "value_1": march, "value_2": ""},
                                        {"if": 10, "op": 2, "value_1": "search_speed", "value_2": ""}
                                    ]

                                    then_clause = [{"then": 49, "value": "speeddeeps", "value_2": ""}]

                                    export_data = {f"{character_server}_{character_name}": []}

                                    # Generate configurations for each name in the item_list
                                    for index, current_name in enumerate(item_list):
                                        # Start with a fresh copy of base conditions for each item
                                        conditions = base_conditions.copy()
                                        
                                        # Add condition for each previous item with "if": 1
                                        for previous_name in item_list[:index]:
                                            conditions.append({"if": 1, "op": 2, "value_1": previous_name, "value_2": ""})
                                        
                                        # Add condition for the current item with "if": 0
                                        conditions.append({"if": 0, "op": 2, "value_1": current_name, "value_2": ""})

                                        # Prepare the configuration for the current set of conditions
                                        config = {
                                            "Enabled": True,
                                            "if": conditions,
                                            "then": then_clause,
                                        }
                                        
                                        # Append the configuration for the current item to export_data
                                        export_data[f"{character_server}_{character_name}"].append(config)





                                
                                with open(export_path, 'w') as export_file:
                                    json.dump(export_data, export_file, indent=4)
                                print(f"Exported conditions for {character_name} in {server_name}.")
                                
                            elif not checked and os.path.exists(export_path):

                                 

                                # Remove the file if it exists and checked is False
                                os.remove(export_path)
                                print(f"Removed condition file for {character_name} in {server_name}, since checked is False.")

def background_task():
    """Background task to send socketio messages."""
    while True:
        processData()
        processMessages()
        speed_condition()
        extract_conditions_data()
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


