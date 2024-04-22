

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
import logging
import re

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
    print("Waiting for gui_done event.")
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




