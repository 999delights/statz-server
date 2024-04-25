

import os
from threading import Thread, Event
import tkinter as tk
from tkinter import filedialog
from tokenize import Double
import eventlet
eventlet.monkey_patch()
from datetime import datetime
from turtle import speed
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
import json
import time
import logging
import re

from server.data.maps import map_map_layers
from server.data.maps import map_dungeon 
from math import atan2, pi




from server.app.utils import calculateAB
from server.app.utils import encode_image
from server.data.maps import map_npcos
from server.data.maps import map_tps_pos
from server.data.maps import map_regions_id_name




app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=5, ping_interval=2, cors_allowed_origins="*")
gui_done = Event()



manager_exe_path = None
silkroad_launcher_path = None
# Global variable declaration
main_directory_path = None  # Initialized as None to signify it's not yet set
info_path = count_path = config_directory_path = ""
statz_directory = msgs_directory = stall_directory = events_directory = ""
messages_dir = tasks_dir = speed_dir = ""





def initialize_directories():
    global main_directory_path, info_path, count_path, config_directory_path
    global statz_directory, msgs_directory, stall_directory, events_directory
    global messages_dir, tasks_dir, speed_dir

    if main_directory_path:
        # Simply define the paths without creating directories or files
        info_path = os.path.join(main_directory_path, 'Plugins', 'info')
        count_path = os.path.join(info_path, 'messages', 'count.json')
        config_directory_path = os.path.join(main_directory_path, 'Config')
        statz_directory = os.path.join(info_path, 'statz')
        msgs_directory = os.path.join(info_path, 'messages', 'msgs')
        stall_directory = os.path.join(info_path, 'stall')
        events_directory = os.path.join(info_path, 'events')

        # Only create these directories if they don't exist
        messages_dir = os.path.join(info_path, 'messages', 'LIVE')
        tasks_dir = os.path.join(info_path, 'tasks')
        speed_dir = os.path.join(tasks_dir, 'speed')

        directories_to_create = [messages_dir, tasks_dir, speed_dir]

        for directory in directories_to_create:
            os.makedirs(directory, exist_ok=True)


# Initialize empty dictionaries to temporarily store the gathered data before sending.
statz_data = {}
messages_data = {}
events_data = {}
speed_data = {}
new_messages_saved = False

speed_pause = False
events_sent = False






###########################################
###########################################
########## DATA FROM INFO FOLDER ##########


def process_events(main_dir):    
    global events_data, events_sent

    events_data = {}
    files_to_delete = []

    if not events_sent:  # Skip processing if events_sent is False
        print("Skipping event processing because events_sent is False.")
        return

    for server in os.listdir(main_dir):
        server_dir = os.path.join(main_dir, server)
        if not os.path.isdir(server_dir):
            continue

        for character in os.listdir(server_dir):
            character_dir = os.path.join(server_dir, character)
            if not os.path.isdir(character_dir):
                continue

            event_files = sorted(os.listdir(character_dir))
            for file_name in event_files:
                file_path = os.path.join(character_dir, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error processing file {file_path}: {e}")
                    continue

                key = next(iter(data))
                event_name = data[key]['event_name']

                if event_name == "EVENT_CONNECTED":
                    connected_event_processed = False
                    for subsequent_file_name in event_files[event_files.index(file_name)+1:]:
                        subsequent_file_path = os.path.join(character_dir, subsequent_file_name)
                        try:
                            with open(subsequent_file_path, 'r') as subsequent_file:
                                subsequent_data = json.load(subsequent_file)
                        except (FileNotFoundError, json.JSONDecodeError) as e:
                            print(f"Error processing file {subsequent_file_path}: {e}")
                            continue

                        subsequent_key = next(iter(subsequent_data))
                        if subsequent_data[subsequent_key]['event_name'] == "EVENT_DISCONNECTED":
                            # Add EVENT_DISCONNECTED to events_data first
                            events_data.setdefault(subsequent_key, []).append(subsequent_data[subsequent_key])
                            # Mark both EVENT_CONNECTED and EVENT_DISCONNECTED for deletion
                            files_to_delete.extend([file_path, subsequent_file_path])
                            connected_event_processed = True
                            break

                    if not connected_event_processed:
                        # If no corresponding EVENT_DISCONNECTED is found, add EVENT_CONNECTED to events_data
                        events_data.setdefault(key, []).append(data[key])
                else:
                    # Directly add events other than "EVENT_CONNECTED" to events_data
                    events_data.setdefault(key, []).append(data[key])

    # Delete marked files after all events have been processed and added to events_data
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except FileNotFoundError:
            print(f"File already deleted: {file_path}")
    events_sent = False
    print("Event processing complete, events_sent reset to False.")

    # Save the extracted data to events.json once after processing all events
    output_file_path = os.path.join(info_path, 'events.json')  # Ensure info_path is correctly defined
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        json.dump(events_data, output_file, indent=4)
    print("Events data saved.")



###########################################
#GET THE STATZ FROM INFO FOLDER  (PLUGIN)
#THIS INCLUDE THE STALL DATA TOO IN THE SAME JSON
def processData():
    global statz_data  # Reference the global variable to update it later

    # Initialize local dictionaries for compiling data
    local_data = {}
    local_stall_data = {}

    # Helper function to read JSON with retries
    def read_json_with_retries(file_path, max_retries=16):
        for attempt in range(max_retries):
            try:
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    return json.load(json_file)
            except json.JSONDecodeError:
                print(f"Attempt {attempt + 1} failed to decode JSON in {file_path}")
                if attempt == max_retries - 1:  # Last attempt also failed
                    print(f"Final attempt to read {file_path} failed.")
                    return None  # or {} if you prefer to return an empty dict instead of None
        return None

    # Process the 'statz' directory for statistical data
    for directory in os.listdir(statz_directory):
        directory_path = os.path.join(statz_directory, directory)
        if os.path.isdir(directory_path):  # Ensure it's a directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):  # Focus on JSON files
                    file_path = os.path.join(directory_path, filename)
                    data = read_json_with_retries(file_path)
                    if data is not None:
                        for key, value in data.items():
                            if key in local_data:  # Merge data into local_data
                                local_data[key].update(value)
                            else:
                                local_data[key] = value

    # Process the 'stall' directory for stall-related activities
    for directory in os.listdir(stall_directory):
        directory_path = os.path.join(stall_directory, directory)
        if os.path.isdir(directory_path):  # Ensure it's a directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):  # Focus on JSON files
                    file_path = os.path.join(directory_path, filename)
                    data = read_json_with_retries(file_path)
                    if data is not None:
                        for key, value in data.items():
                            if key in local_stall_data:  # Merge data into local_stall_data
                                local_stall_data[key].update(value)
                            else:
                                local_stall_data[key] = value

    # Merge local_stall_data into local_data
    for key, value in local_stall_data.items():
        if key in local_data:
            local_data[key].update(value)

     # Update the global statz_data with the compiled local_data
    for key, value in local_data.items():
        if key in statz_data:
            # If the key exists in statz_data, update it
            statz_data[key].update(value)
        else:
            # If the key doesn't exist, add it to statz_data
            statz_data[key] = value


###########################################
#GET THE SPEED FROM INFO FOLDER  (PLUGIN)
def processSpeed():
    global speed_data  # Reference the global variable to update it later
    global speed_pause

    # Initialize local dictionaries for compiling data
    local_data = {}
    # Helper function to read JSON with retries
    def read_json_with_retries(file_path, max_retries=16):
        for attempt in range(max_retries):
            try:
                with open(file_path, 'r', encoding='utf-8') as json_file:
                    return json.load(json_file)
            except json.JSONDecodeError:
                print(f"Attempt {attempt + 1} failed to decode JSON in {file_path}")
                if attempt == max_retries - 1:  # Last attempt also failed
                    print(f"Final attempt to read {file_path} failed.")
                    return None  # or {} if you prefer to return an empty dict instead of None
        return None
    if speed_pause == False:
        speed_data = {}
       
        for directory in os.listdir(speed_dir):
            directory_path = os.path.join(speed_dir, directory)
            if os.path.isdir(directory_path):  # Ensure it's a directory
                for filename in os.listdir(directory_path):
                    if filename.endswith(".json"):  # Focus on JSON files
                        file_path = os.path.join(directory_path, filename)
                        
                        data = read_json_with_retries(file_path)
                        if data is not None:
                           
                            for key, value in data.items():
                              
                                if key in local_data:  # Merge data into local_data
                                    local_data[key].update(value)
                                else:
                                    local_data[key] = value


        # Update the global statz_data with the compiled local_data
        for key, value in local_data.items():
            if key in speed_data:
                # If the key exists in statz_data, update it
                speed_data[key].update(value)
            else:
                # If the key doesn't exist, add it to statz_data
                speed_data[key] = value
        output_file_path = os.path.join(info_path, 'speed.json')
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(speed_data, output_file, indent=4)

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
# @app.route('/phBotHTTP', methods=['POST'])
# def phBotHTTP():
#     global manager_data
#     manager_data = {}
#     data = request.form.get('data')
#     if data:
#         # Replace "1.#INF" with null in the data string
#         cleaned_data = data.replace("1.#INF", "null")

#         # Load the modified JSON data as a dictionary
#         data_dict = json.loads(cleaned_data)

#         # Remove the 'time_to_level' field from each sub-dictionary
#         for key in data_dict:
#             if 'time_to_level' in data_dict[key]:
#                 del data_dict[key]['time_to_level']

#         # Set the modified dictionary as the latest_data
#         manager_data = data_dict

#         return "Data received and stored for process1"
#     else:
#         return "No data received"
############################################ 



############## FROM HELPER ################
###########################################
###########################################





###########################################
###########################################
############## FROM CLIENT ################



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
# SEND STATZ (FROM PLUGIN) TO CLIENT
###########################################
        


socketio.on('fetch_SPEED')
def handle_fetch_speed():

    global speed_pause

    if not speed_pause and speed_data:
                # Emit the events data via socket
        socketio.emit('characters_speed', speed_data)
    else:
        # Emit an error message if no data is available
        socketio.emit('speed_error', 'No data available yet.')


socketio.on('fetch_EVENTS')
def handle_fetch_events():

    global events_sent

    if events_sent == False:
                # Emit the events data via socket
        socketio.emit('characters_events', events_data)
        events_sent = True

    else:
        # Emit an error message if no data is available
        socketio.emit('events_error', 'No data available yet.')








socketio.on('fetch_STATZ')
def handle_fetch_characters():
    global statz_data  # Assuming statz_data is a global variable holding stats

    local_statz_data = statz_data.copy()  # Create a local copy of statz_data
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

#rx
@socketio.on('speed_cast')
def handle_speed_cast(payload):
    global speed_pause
    speed_pause = True
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

    speed_pause = False

#rx
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


# def extract_conditions_data():
   

#     # Create a dictionary to store conditions data for each file
#     conditions_data = {}

#     # Define a regular expression pattern to match the filename pattern "server_character.json"
#     filename_pattern = re.compile(r'^(.+)_(.+)\.json$')

#     # Iterate over files in the config directory
#     for file_name in os.listdir(config_directory_path):
#         if file_name.endswith('.json'):
#             # Check if the filename matches the pattern
#             match = filename_pattern.match(file_name)
#             if match:
#                 server = match.group(1)
#                 character = match.group(2)





#                 file_path = os.path.join(config_directory_path, file_name)
#                 with open(file_path, 'r', encoding='utf-8') as json_file:
#                     try:
#                         data = json.load(json_file)
#                         conditions_data[f"{server}_{character}"] = data.get('Conditions', {})
#                     except (json.JSONDecodeError, ValueError):
#                         print(f"Error processing file {file_path}")
          

#     # Save the extracted data to conditions.json in main_directory_path
#     output_file_path = os.path.join(info_path, 'conditions.json')
#     with open(output_file_path, 'w', encoding='utf-8') as output_file:
#         json.dump(conditions_data, output_file, indent=4)

######### DATA FROM CONFIG FOLDER #########
###########################################
###########################################




 # OLD URL SYSTEM TO SEND STATS   
@app.route('/characters', methods=['GET'])
def get_characters():

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
        
    return statz_data  # Return the dictionary as JSON
      




#Images
base_path = 'lib/images/'
npcImage =  base_path + 'mm_sign_npc.jpg'
charImage = base_path + 'mm_sign_character.png'
monsterImage = base_path + 'mm_sign_monster.jpg'
ptImage = base_path + 'mm_sign_party.jpg'
ptImageSelected = base_path + 'mm_sign_party2.jpg'
pplImage = base_path + 'mm_sign_otherplayer.jpg'
defaultImage = base_path + 'DEFAULTMAP.png'

prevA = None
prevB = None
prevAX = None
prevBY = None
rotationAngle = float(0)
lastDirection = 'No Direction'

def calculate_map_data(character_name,job_name, server_name ,character,width):
    global prevA
    global prevB
    global prevAX
    global prevBY
    global rotationAngle
    global lastDirection
    
    backgroundChanged = False
    
    
   
    npcPositions = []
    tpsPositions = []
    monstersPositions = []
    ptPositions = []
    selectedPositions = []
    pplPositions = []
    trainingPosition = []
    charPosition = []
    region_name = ''
    images = []
    #char initials

    region = character['position']['region']
    x = character['position']['x']
    y = character['position']['y']
    z = character['position']['z']
    path = path_finder(region)
    a = 0
    b = 0
    x2 = 0
    y2 = 0
    aX = 0
    bY = 0
    prefix = ''

    
    try:
        # Attempt to fetch the region name directly
        region_name = map_regions_id_name.idNameMapp[str(region)]
    except KeyError:
        # If direct fetch fails, try with adjusted region key
        try:
            adjusted_region = region - 65536
            region_name = map_regions_id_name.idNameMapp[str(adjusted_region)]
        except KeyError:
            # If both attempts fail, return an empty string
            region_name = ""

    #training area initials
    xTr = character["training_area"]['x']
    yTr = character["training_area"]['y']
    zTr = character["training_area"]['z']
    regionTr = character["training_area"]['region']
    radius = character["training_area"]['radius']
    aTr = 0
    bTr = 0
    x2Tr = 0
    y2Tr = 0
    axTr = 0
    byTr = 0

    #mobs initials
    monsters = character['monsters']
    xM = 0
    yM = 0
    regionM = 0
    aM = 0
    bM = 0
    axM = 0
    byM = 0
    x2M = 0
    y2M = 0

    #party initials
    party = character['party']
    isPartyNotEmpty = bool(party)
    xPt = 0
    yPt = 0
    regionPt = 0
    aPt = 0
    bPt = 0
    axPt = 0
    byPt = 0
    x2Pt = 0
    y2Pt = 0

    #other players initials
    ppl = {}
    xPpl = 0
    yPpl = 0
    regionPpl = 0
    aPpl = 0
    bPpl = 0
    axPpl = 0
    byPpl = 0
    x2Ppl = 0
    y2Ppl = 0




    #calculate

    ##for tr
    tr = calculate_ab(regionTr,xTr,yTr,zTr,aTr,bTr,axTr,byTr,x2Tr,y2Tr,False, prefix = None)

    ##for char
    print("char"+ prefix)
    char = calculate_ab( region,x, y, z,a,b,aX,bY,x2,y2,False, prefix= prefix)


    #grid

    gridA = position_values_a(char.a)
    gridB = position_values_b(char.b)
    posLeft = positions_left(width)
    posTop = positions_top(width)

    lastDirection = determine_direction(prevAX,prevBY,char.ax,char.by,prevA,prevB, char.a,char.b )
    
    if isinstance(lastDirection, float):
        rotationAngle = lastDirection

    
    def has_a_or_b_changed():
        return prevA != char.a or prevB != char.b
    
            # Determine if there has been a change
    a_or_b_changed = has_a_or_b_changed()

    # Set animation duration based on whether there was a change
    animation_duration = 0 if a_or_b_changed else 300
    
    prevAX = char.ax
    prevBY = char.by
 
    prevA = char.a
    prevB = char.b

    offsetX = width * -char.by /2 
    offsetY = width * -char.ax /2

   


    for i in range(3):  # iterating over three rows
        for j in range(3):  # iterating over three columns
            image_path = f"{path}{char.prefix}{int(gridA[i][j])}x{int(gridB[i][j])}.jpg"
            # Create a dictionary for each image with its path and positions
            item = {
                'image': image_path,
                'left': posLeft[i][j],
                'top': posTop[i][j]
            }
            images.append(item)


    regionCombinations = generate_regions_from_ab_combinations(gridA, gridB,char.region)




    #TRAINING AREA CALCULATE
    for r in regionCombinations:
      
        
        
        if regionTr == int(r):
            # Check proximity conditions
            condition2CheckaTr = tr.a in [char.a- 1, char.a, char.a + 1]
            condition3CheckbTr = tr.b in [char.b - 1, char.b, char.b + 1]
            
            if condition2CheckaTr and condition3CheckbTr:
                # Calculate positions
                left = calculate_position(tr.a, char.a, tr.b, char.b, tr.ax, tr.by, True, posLeft)
                bottom = calculate_position(tr.a, char.a, tr.b, char.b, tr.ax, tr.by, False, posTop)
                
                # Set position with radius in the dictionary
                trainingPosition.append({
                    'left': left - radius,  # Adjust to center the circle
                    'bottom': bottom - radius,
                    'radius': radius
                })
                

    #PARTY CALCULATE
    for key, value in party.items():
        xPt = value['x']
        yPt = value['y']
        regionPt = value['region']
        playerName = value['name']

        # Calculate position for each party member
        pt = calculate_ab(regionPt, xPt, yPt, 0, aPt, bPt, axPt, byPt, x2Pt, y2Pt, False, None)

        # Check proximity conditions
        condition1CheckaNpc = pt.a in [char.a - 1, char.a, char.a + 1]
        condition2CheckbNpc = pt.b in [char.b - 1, char.b, char.b + 1]

        if condition1CheckaNpc and condition2CheckbNpc:
            # Calculate left and bottom positions
            left = calculate_position(pt.a, char.a, pt.b, char.b, pt.ax, pt.by, True, posLeft)
            bottom = calculate_position(pt.a, char.a, pt.b, char.b, pt.ax, pt.by, False, posTop)
            if playerName != character_name and job_name != playerName:
                # Append the calculated positions to ptPositions

                pt_entry = {
                    'playerName': playerName,
                    'left': left,
                    'bottom': bottom,
                    'image': ptImage  # Assuming a generic path or use a condition to determine the image

                }
                ptPositions.append(pt_entry)


    #mobs calculate
    for key, value in monsters.items():
        xM = value['x']
        yM = value['y']
        regionM = value['region']

        # Calculate the AB position for the monster
        monster = calculate_ab(regionM, xM, yM, 0, aM, bM, axM, byM, x2M, y2M, False, None)

        # Check if the monster is in proximity to the character
        condition1CheckaNpc = monster.a in [char.a - 1, char.a, char.a + 1]
        condition2CheckbNpc = monster.b in [char.b - 1, char.b, char.b + 1]

        if condition1CheckaNpc and condition2CheckbNpc:
            left = calculate_position(monster.a, char.a, monster.b, char.b, monster.ax, monster.by, True, posLeft)
            bottom = calculate_position(monster.a, char.a, monster.b, char.b, monster.ax, monster.by, False, posTop)

            # Append the position and the path of the monster image
            monster_entry = {                
                'left': left,
                'bottom': bottom,
                "image": monsterImage
               }
            monstersPositions.append(monster_entry)

    #ppl calculate
    for key, value in ppl.items():
        regionPpl = int(value.get('Region ID', 0))
        xPpl = float(value['posx'])
        yPpl = float(value['posy'])

        # Adjust region if necessary
        if regionPpl > 32767:
            regionPpl -= 65536

        # Calculate the AB position for the other player
        otherP = calculate_ab(regionPpl, xPpl, yPpl, 0, aPpl, bPpl, axPpl, byPpl, x2Ppl, y2Ppl, True, None)

        # Check proximity conditions
        condition1CheckaNpc = otherP.a in [char.a - 1, char.a, char.a + 1]
        condition2CheckbNpc = otherP.b in [char.b - 1, char.b, char.b + 1]

        if condition1CheckaNpc and condition2CheckbNpc:
            left = calculate_position(otherP.a, char.a, otherP.b, char.b, otherP.ax, otherP.by, True, posLeft)
            bottom = calculate_position(otherP.a, char.a, otherP.b, char.b, otherP.ax, otherP.by, False, posTop)

            # Append the calculated positions along with the image path
            ppl_entry = {
                'left': left,
                'bottom':bottom,
                'image': pplImage

            }
            pplPositions.append(ppl_entry)

    #npc calculate
    for r in regionCombinations:
        
        if str(r) in map_npcos.npcPos:
            print(str(r) + "found")
            npcs_in_region = map_npcos.npcPos[str(r)]

            for npc in npcs_in_region:
                
                x_npc = float(npc['x'])
                y_npc = float(npc['y'])
                z_npc = float(npc['z'])
                npc_region = int(npc['region'])
                a_npc = b_npc = int(0)
                x2_npc = y2_npc = ax_npc = by_npc = float(0)
                
                # Assume calculate_ab and calculate_position are defined functions
                vendor = calculate_ab(npc_region, x_npc, y_npc, z_npc, a_npc, b_npc, ax_npc, by_npc, x2_npc, y2_npc, True, prefix = None)

                condition1CheckaNpc = vendor.a in [char.a - 1, char.a, char.a + 1]
                condition2CheckbNpc = vendor.b in [char.b - 1, char.b, char.b + 1]
                
                if condition1CheckaNpc and condition2CheckbNpc:
                    left = calculate_position(vendor.a, char.a, vendor.b, char.b, vendor.ax, vendor.by, True, posLeft)
                    bottom = calculate_position(vendor.a, char.a, vendor.b, char.b, vendor.ax, vendor.by, False, posTop)
                    
                    npc_entry = {
                        'left': left,
                        'bottom': bottom,
                        "image": npcImage,
                    }
                    npcPositions.append(npc_entry)
                    print(npcPositions)
    #tp calculate
    for r in regionCombinations:
        
        if str(r) in map_tps_pos.tpsPos: 
           
            tps_in_region = map_tps_pos.tpsPos[str(r)]
            
            for tp in tps_in_region:
                x_tp = float(tp['x'])
                y_tp = float(tp['y'])
                z_tp = float(tp['z'])
                tp_region = int(tp['region'])
                type = int(tp['type'])
                
                a_tp = b_tp = x2_tp = y2_tp = ax_tp = by_tp = 0  # Initialize to default values

                # Calculate the AB position for the teleport
                tport = calculate_ab(tp_region, x_tp, y_tp, z_tp, a_tp, b_tp, ax_tp, by_tp, x2_tp, y2_tp, True, prefix = None)

                # Check proximity conditions
                condition1_check_tp = tport.a in [char.a - 1, char.a, char.a + 1]
                condition2_check_tp = tport.b in [char.b - 1, char.b, char.b + 1]
                
                if condition1_check_tp and condition2_check_tp:
                   
                    left = calculate_position(tport.a, char.a, tport.b, char.b, tport.ax, tport.by, True, posLeft) - 8.5
                    bottom = calculate_position(tport.a, char.a, tport.b, char.b, tport.ax, tport.by, False, posTop) - 8.5

                    pathTp = get_icon_path(type)  # Assuming a function to determine path from type
                   
                    teleport_entry = {
                        'left': left,
                        'bottom': bottom,
                        'image':pathTp
                    }
                    tpsPositions.append(teleport_entry)
                    print(tpsPositions)


    #char position
    left = posLeft[1][1] + (char.ax * posLeft[1][1])
    bottom = posTop[1][1] + (char.by * posTop[1][1])
    
    charPosition.append({
        'left':left,
        'bottom': bottom,
        'image': charImage
    })
    # Include more calculations as needed
    return {
       
        "npcPos": npcPositions, 
            "tpsPos": tpsPositions,
            "mobPos": monstersPositions,
            "ptPos": ptPositions,
            "pplPos": pplPositions,
            "trPos": trainingPosition,
            "charPos": charPosition,
            "regionName": region_name,
            "images": images,
            "animationD": animation_duration,
            "offsetX": offsetX,
            "offsetY": offsetY,
            "rotationAngle": rotationAngle,
            'defaultImage': defaultImage,
         
    }



def map_engine(character_name, server_name, width):
    # Construct the key from character_name and server_name
    key = f"{character_name}/{server_name}"
    
    # Access the data directly using the constructed key
    character_data = statz_data.get(key)
    
    # Check if we have data for the given key
    if character_data:
        job_name = character_data['job_name']
        result = calculate_map_data(character_name, job_name, server_name, character_data, width)
        return result
    else:
        # Return an empty dictionary if no data found for the key
        return {}










def generate_regions_from_ab_combinations(grid_a, grid_b,region_value):
    """
    Generates a list of unique region codes based on combinations of values from grid_a and grid_b.
    The combination is done by shifting values from grid_b by 8 bits and merging with values from grid_a.
    The result is adjusted to ensure it fits within a 16-bit signed integer range.

    Args:
        grid_a (List[List[int]]): Grid of values for 'A' combinations, representing lower 8 bits.
        grid_b (List[List[int]]): Grid of values for 'B' combinations, representing upper 8 bits.

    Returns:
        List[int]: A list of unique region codes.
    """
    regions = set()  # Using set for better performance in membership testing

    for i in range(len(grid_a)):
        for j in range(len(grid_a[i])):
            # Convert floats to integers if necessary
            a_value = int(grid_a[i][j])
            b_value = int(grid_b[i][j])

            region = (b_value << 8) | a_value

            # Adjust if the value exceeds the max positive value for a 16-bit signed integer.
            if region > 32767:
                region = region_value - 65536  # Ensures values wrap within signed 16-bit range

            regions.add(region)

    return list(regions)  # Convert set





def determine_direction(prev_ax, prev_by, current_ax, current_by, prev_a, prev_b, current_a, current_b):
    """
    Determines the direction of movement or if the image has changed.

    Args:
    prev_ax (float or None): Previous x-coordinate.
    prev_by (float or None): Previous y-coordinate.
    current_ax (float): Current x-coordinate.
    current_by (float): Current y-coordinate.
    prev_a (int or None): Previous A index.
    prev_b (int or None): Previous B index.
    current_a (int): Current A index.
    current_b (int): Current B index.

    Returns:
    str or float: Descriptive string or angle in radians.
    """
    # Check if the image has changed
    if str(prev_a) != str(current_a) or str(prev_b) != str(current_b):
       
        return 'Image Changed'

    print(f"current_ax: {current_ax}, prev_ax: {prev_ax}")
    print(f"current_by: {current_by}, prev_by: {prev_by}")

    delta_x = float((current_ax - prev_ax if prev_ax is not None else 0.0))
    delta_y = float((current_by - prev_by if prev_by is not None else 0.0))

    print(f"delta_x: {delta_x}, delta_y: {delta_y}")
    # If no movement
    if delta_x == 0.0 and delta_y == 0.0:
        print("prevA" + str(prev_a))
        print("-ax" + str(current_ax - prev_ax))
        print("prevB" + str(prev_b))
        print("-by" + str(current_by - prev_by))
        return 'No Direction'

    # Calculate angle in degrees, then convert to radians
    angle_deg = float(atan2(-delta_y, delta_x) * (180 / pi))
    print("ANGLE" + str(float(angle_deg * (pi / 180))))
    return float(angle_deg * (pi / 180))





def position_values_a2(a):
    return [[a - 2, a - 1, a, a + 1, a + 2] for _ in range(5)]

def position_values_b2(b):
    return [[b + i] * 5 for i in range(2, -3, -1)]

def position_values_a(a):
    return [[a - 1, a, a + 1] for _ in range(3)]

def position_values_b(b):
    return [[b + 1] * 3, [b] * 3, [b - 1] * 3]

def positions_left(width):
    half_width = width / 2
    return [
        [0.0, half_width, width],
        [0.0, half_width, width],
        [0.0, half_width, width]
    ]

def positions_top(width):
    half_width = width / 2
    return [
        [0.0, 0.0, 0.0],
        [half_width, half_width, half_width],
        [width, width, width]
    ]











def path_finder(region):
    """Determines the path to image resources based on the region ID."""
    base_path = 'lib/images/minimap/'  # Corrected relative path from app/utils/
    if region >= 0:
        return base_path  # Non-dungeon path
    else:
        return base_path + 'd/'  # Dungeon path
    


def get_icon_path(type):
    # Define the base path where all images are stored
    base_path = 'lib/images/'

    if type == 1:  # fortress
        return base_path + 'fort_worldmap.png'
    elif type == 2:  # gate of ress
        return base_path + 'strut_revival_gate.png'
    elif type == 3:  # gate of glory
        return base_path + 'strut_glory_gate.png'
    elif type == 4:  # fortress small
        return base_path + 'fort_small_worldmap.png'
    elif type == 5:  # ground teleport
        return base_path + 'map_world_icontel.png'
    elif type == 6:  # tahomet
        return base_path + 'tahomet_gate.png'
    else:  # gate or any other type
        return base_path + 'xy_gate.png'



def calculate_position(a1, a2, b1, b2, aX, bY, calculate_left, positions):
    position = 0.0

    condition2_check_a = a1 == a2 or a1 == a2 + 1 or a1 == a2 - 1
    condition3_check_b = b1 == b2 or b1 == b2 + 1 or b1 == b2 - 1

    if condition2_check_a and condition3_check_b:
        if a1 == a2 and b1 == b2:
            # Central position
            if calculate_left:
                position = positions[1][1] + (aX * positions[1][1])
            else:
                position = positions[1][1] + (bY * positions[1][1])
        elif a1 == a2 + 1 and b1 == b2 - 1:
            # Bottom-Right
            if calculate_left:
                position = positions[0][2] + (aX * positions[1][1])
            else:
                position = positions[0][2] + (bY * positions[1][1])
        elif a1 == a2 + 1 and b1 == b2:
            # Right
            if calculate_left:
                position = positions[1][2] + (aX * positions[1][1])
            else:
                position = positions[1][2] + (bY * positions[1][1])
        elif a1 == a2 + 1 and b1 == b2 + 1:
            # Top-Right
            if calculate_left:
                position = positions[2][2] + (aX * positions[1][1])
            else:
                position = positions[2][2] + (bY * positions[1][1])
        elif a1 == a2 and b1 == b2 + 1:
            # Top
            if calculate_left:
                position = positions[2][1] + (aX * positions[1][1])
            else:
                position = positions[2][1] + (bY * positions[1][1])
        elif a1 == a2 - 1 and b1 == b2 + 1:
            # Top-Left
            if calculate_left:
                position = positions[2][0] + (aX * positions[1][1])
            else:
                position = positions[2][0] + (bY * positions[1][1])
        elif a1 == a2 - 1 and b1 == b2:
            # Left
            if calculate_left:
                position = positions[1][0] + (aX * positions[1][1])
            else:
                position = positions[1][0] + (bY * positions[1][1])
        elif a1 == a2 - 1 and b1 == b2 - 1:
            # Bottom-Left
            if calculate_left:
                position = positions[0][0] + (aX * positions[1][1])
            else:
                position = positions[0][0] + (bY * positions[1][1])
        elif a1 == a2 and b1 == b2 - 1:
            # Bottom
            if calculate_left:
                position = positions[0][1] + (aX * positions[1][1])
            else:
                position = positions[0][1] + (bY * positions[1][1])

    return position





class CalculationResult:
    def __init__(self, region, a, b, x, y, z, ax, by, x2, y2, prefix):
        self.region = region
        self.a = a
        self.b = b
        self.x = x
        self.y = y
        self.z = z
        self.ax = ax
        self.by = by
        self.x2 = x2
        self.y2 = y2
        self.prefix = prefix

def calculate_ab(region, x, y, z, a, b, ax, by, x2, y2, npc, prefix):
    if region >= 0:
        if npc:
            
            a = region_to_a_nd(region)
            b = region_to_b_nd(region)
            ax = get_npc_ax_nd(x)
            by = get_npc_ay_nd(y)
        else:
            a = get_A_ND(x)
            b = get_B_ND(y)
            ax = get_aX_ND(x)
            by = get_bY_ND(y)
    else:
        region += 65536
        if npc:
            a = get_A_D(x)
            b = get_B_D(y)
            ax = get_aX_D(x)
            by = get_bY_D(y)
        else:
            x2 = getNew_X(x, region)
            y2 = getNew_Y(y, region)
            a = get_A_D(x2)
            b = get_B_D(y2)
            ax = get_aX_D(x2)
            by = get_bY_D(y2)

        if region == 32769 and prefix is not None:
            if z <= 115:
                region = 327691
            elif z < 230:
                region = 327692
            elif z < 345:
                region = 327693
            else:
                region = 327694
       
        
        if prefix is not None and prefix == '' and region in map_map_layers.regionImagePrefixes:
           
            prefixes = map_map_layers.regionImagePrefixes[region]
            for candidate_prefix in prefixes:
                print(candidate_prefix)
                if try_load_images(candidate_prefix, a, b):
                    prefix = candidate_prefix
                    print(f"Loaded images with prefix: {prefix}")
                    break

    return CalculationResult(region, a, b, x, y, z, ax, by, x2, y2, prefix)

def try_load_images(prefix, a, b):
    # Construct the image dimension key as a string
    axb_value = f"{int(a)}x{int(b)}"
    # Removing the last underscore only if it exists and is the last character
    if prefix.endswith('_'):
        modified_prefix = prefix[:-1]
    else:
        modified_prefix = prefix
    # Check if the prefix exists and the specific dimension is included
    return modified_prefix in map_dungeon.imagesMapD and axb_value in map_dungeon.imagesMapD[modified_prefix]



def isInTrainingArea(characterPosition, trainingArea):
    if not characterPosition or not trainingArea:
        return False

    radius = trainingArea['radius']

    if characterPosition['region'] == trainingArea['region']:
        if characterPosition['region'] >= 0:
            # For non-dungeon
            charAX = get_aX_ND(characterPosition['x'])
            charBY = get_bY_ND(characterPosition['y'])
            charA = get_A_ND(characterPosition['x'])
            charB = get_B_ND(characterPosition['y'])

            trainingAX = get_aX_ND(trainingArea['x'])
            trainingBY = get_bY_ND(trainingArea['y'])
            trainingA = get_A_ND(trainingArea['x'])
            trainingB = get_B_ND(trainingArea['y'])

            return (charA == trainingA and
                    charB == trainingB and
                    abs(charAX - trainingAX) <= radius and
                    abs(charBY - trainingBY) <= radius)

        else:
            # For dungeon
            charX2 = getNew_X(characterPosition['x'], characterPosition['region'])
            charY2 = getNew_Y(characterPosition['y'], characterPosition['region'])
            charAX = get_aX_D(charX2)
            charBY = get_bY_D(charY2)
            charA = get_A_D(charX2)
            charB = get_B_D(charY2)

            trainingX2 = getNew_X(trainingArea['x'], trainingArea['region'])
            trainingY2 = getNew_Y(trainingArea['y'], trainingArea['region'])
            trainingAX = get_aX_D(trainingX2)
            trainingBY = get_bY_D(trainingY2)
            trainingA = get_A_D(trainingX2)
            trainingB = get_B_D(trainingY2)

            return (charA == trainingA and
                    charB == trainingB and
                    abs(charAX - trainingAX) <= radius/200 and
                    abs(charBY - trainingBY) <= radius/200)
    
    return False



def region_to_a_nd(region):
    """Extract the 'A' value from the region code by applying a bitwise AND to get the lowest byte."""
    return region & 0xFF

def region_to_b_nd(region):
    """Extract the 'B' value from the region code by shifting right by 8 bits to move the second lowest byte to the lowest byte position."""
    return region >> 8

def get_npc_ax_nd(x):
    """Calculate the NPC 'aX' value for Non-Dungeon based on the given x-coordinate."""
    return (256 / 1920 * x) / 256 - 0.015

def get_npc_ay_nd(y):
    """Calculate the NPC 'bY' value for Non-Dungeon based on the given y-coordinate."""
    return (256 / 1920 * y) / 256 - 0.04


# GET A NON DUNGEON
def get_A_ND(x):
    return int(x / 192 + 135)

# GET B NON DUNGEON
def get_B_ND(y):
    return int(y / 192 + 92)

# GET A DUNGEON
def get_A_D(x):
    return (128 * 192 + x / 10) // 192

# GET B DUNGEON
def get_B_D(y):
    return (128 * 192 + y / 10) // 192

# GET aX NON DUNGEON
def get_aX_ND(x):
    return (x / 192 + 135) - (x / 192 + 135) // 1 - 0.015

# GET bY NON DUNGEON
def get_bY_ND(y):
    return (y / 192 + 92) - (y / 192 + 92) // 1 - 0.04

# GET aX DUNGEON
def get_aX_D(x):
    value = (128 * 192 + x / 10) / 192
    return value - value // 1 - 0.015

# GET bY DUNGEON
def get_bY_D(y):
    value = (128 * 192 + y / 10) / 192
    return value - value // 1 - 0.04

# GET newX
def getNew_X(x, region):
    return 10 * (x - ((region & 255) - 128) * 192)

# GET newY
def getNew_Y(y, region):
    return 10 * (y - ((region >> 8) - 128) * 192)




@socketio.on('map')
def handle_map_data(payload):
    print(f"Received map_data from")  # Log the socket ID
    print(payload)  # Debug print the received payload

    character_name = payload['character']
    print(character_name)
    server_name = payload['server']
    width = payload['width']
    print(width)
    result = map_engine(character_name, server_name, width)
    socketio.emit('map_data',result)
    print('emitted')



def background_task():
    """Background task to send socketio messages."""
    while True:
        processData()
        processMessages()
        processSpeed()
        

        #extract_conditions_data()  # config

        handle_fetch_characters()
        handle_fetch_messages() 
        handle_fetch_events()
        handle_fetch_speed()
        process_events(events_directory)
        time.sleep(3)  

def run_gui():
    global main_directory_path, manager_exe_path, silkroad_launcher_path  # Declare global variables

    # Initialize the variables
    main_directory_path = ""
    manager_exe_path = ""
    silkroad_launcher_path = ""

    def select_path(var_name):
        path = filedialog.askdirectory() if var_name == "main_directory_path" else filedialog.askopenfilename()
        if path:
            globals()[var_name] = path  # Update the global variable with the selected path
            if all([main_directory_path, manager_exe_path, silkroad_launcher_path]):
                start_server_button['state'] = 'normal'  # Enable the button if all paths are selected
            labels[var_name].config(text=path)  # Update the label with the selected path

    window = tk.Tk()
    window.title("Select Required Paths")
    # Maximize the window
    window.state('zoomed')

    # Using a frame to easily center widgets
    center_frame = tk.Frame(window)
    center_frame.pack(expand=True)

    labels = { 
        "main_directory_path": tk.Label(center_frame, text="No directory selected"),
        "manager_exe_path": tk.Label(center_frame, text="No file selected"),
        "silkroad_launcher_path": tk.Label(center_frame, text="No file selected")
    }

    # Adjusting the grid and adding more space between buttons and labels
    tk.Button(center_frame, text="Browse phBot Directory", command=lambda: select_path("main_directory_path")).grid(row=0, column=0, pady=(10, 2), padx=10)
    labels["main_directory_path"].grid(row=1, column=0, pady=(2, 10), padx=10)
    tk.Button(center_frame, text="Browse Manager.exe", command=lambda: select_path("manager_exe_path")).grid(row=2, column=0, pady=(10, 2), padx=10)
    labels["manager_exe_path"].grid(row=3, column=0, pady=(2, 10), padx=10)
    tk.Button(center_frame, text="Browse Silkroad Launcher", command=lambda: select_path("silkroad_launcher_path")).grid(row=4, column=0, pady=(10, 2), padx=10)
    labels["silkroad_launcher_path"].grid(row=5, column=0, pady=(2, 10), padx=10)

    start_server_button = tk.Button(center_frame, text="Start Server", state='disabled', command=lambda: gui_done.set() or window.destroy())
    start_server_button.grid(row=6, column=0, pady=20, padx=10)

    window.mainloop()

def start_server():
    print("from start_server: Waiting for gui_done event.")
    """Starts the Flask and SocketIO server after GUI is done."""
    gui_done.wait()  # Wait for the GUI to finish
    print("gui_done event received, starting server.")
    if main_directory_path:
        initialize_directories()
        socketio.start_background_task(background_task)
        print("Server starting...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    else:
        print("No directory was selected. Server not started.")

if __name__ == '__main__':
    gui_thread = Thread(target=run_gui)
    gui_thread.start()
    gui_thread.join()  # Wait for the GUI thread to finish
    start_server()






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

