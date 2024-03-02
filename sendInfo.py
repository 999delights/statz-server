import os
import json
import http.client
import time

# Main directory path
main_directory_path = r'C:\Users\andre\AppData\Local\Programs\phBot Testing\Plugins\info'

# Additional directories
statz_directory = main_directory_path + r'\statz'
msgs_directory = main_directory_path + r'\messages\msgs'
stall_directory = main_directory_path + r'\stall'

# Initialize empty dictionaries to store data
all_data = {}
all_messages = {}
stall_data = {}


while True:
    # Loop through all directories in the statz directory
    for directory in os.listdir(statz_directory):
        directory_path = os.path.join(statz_directory, directory)
        
        # Check if the item is a directory
        if os.path.isdir(directory_path):
            # Iterate over files within the directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(directory_path, filename)

                    # Open and read the JSON file
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        try:
                            # Load the JSON data into a dictionary
                            data = json.load(json_file)

                            # Iterate over the data dictionary to merge it into all_data
                            for key, value in data.items():
                                if key in all_data:
                                    # If the key already exists, append the new data to the existing dictionary
                                    all_data[key].update(value)
                                else:
                                    # If the key is new, add it to the all_data dictionary
                                    all_data[key] = value

                        except json.JSONDecodeError:
                            print(f"Error decoding JSON in {filename}")
                            continue

                    # If filename starts with 'player_', clear its contents
                    if filename.startswith('player_'):
                        with open(file_path, 'w', encoding='utf-8') as file_to_clear:
                            file_to_clear.write('')

     # Loop through all directories in the stall directory
    for directory in os.listdir(stall_directory):
        directory_path = os.path.join(stall_directory, directory)
        
        # Check if the item is a directory
        if os.path.isdir(directory_path):
            # Iterate over files within the directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(directory_path, filename)

                    # Open and read the JSON file
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        try:
                            # Load the JSON data into a dictionary
                            data = json.load(json_file)

                            # Iterate over the data dictionary to merge it into stall_data
                            for key, value in data.items():
                                if key in stall_data:
                                    # If the key already exists, append the new data to the existing dictionary
                                    stall_data[key].update(value)
                                else:
                                    # If the key is new, add it to the all_data dictionary
                                    stall_data[key] = value

                        except json.JSONDecodeError:
                            print(f"Error decoding JSON in {filename}")
                            continue

    for key, value in stall_data.items():
        if key in all_data:
            # If the key already exists in all_data, update its value
            all_data[key].update(value)


    # Loop through all directories in the msgs directory
    for directory in os.listdir(msgs_directory):
        directory_path = os.path.join(msgs_directory, directory)
        
        # Check if the item is a directory
        if os.path.isdir(directory_path):
            # Iterate over files within the directory
            for filename in os.listdir(directory_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(directory_path, filename)

                    # Open and read the JSON file
                    with open(file_path, 'r', encoding='utf-8') as json_file:
                        try:
                            # Load the JSON data into a dictionary
                            data = json.load(json_file)

                            # Iterate over the data dictionary to merge it into all_messages
                            for key, value in data.items():
                                if key in all_messages:
                                    # If the key already exists, append the new data to the existing dictionary
                                    all_messages[key].update(value)
                                else:
                                    # If the key is new, add it to the all_messages dictionary
                                    all_messages[key] = value

                        except json.JSONDecodeError:
                            print(f"Error decoding JSON in {filename}")
                            continue

                    # If filename starts with 'message_', clear its contents
                    if filename.startswith('message_'):
                        with open(file_path, 'w', encoding='utf-8') as file_to_clear:
                            file_to_clear.write('')




    # Count the number of messages (msgs and dmTOmsgs) for each character
    character_message_counts = {}
    for character, character_data in all_messages.items():
        msgs_count = len(character_data.get('msgs', []))
        dmTOmsgs_count = len(character_data.get('dmTOmsgs', []))
        character_message_counts[character] = {
            'msgs': msgs_count,
            'dmTOmsgs': dmTOmsgs_count
        }

    # Convert the combined data to JSON strings
    json_data = json.dumps(all_data)
    json_messages = json.dumps(all_messages)
    json_message_counts = json.dumps(character_message_counts)

    # Send the JSON data to the specified URL
    conn_data = http.client.HTTPConnection('192.168.1.85', 5000)
    path_data = '/STATZ'  # Path for data
    headers_data = {'Content-Type': 'application/json'}

    # Send the JSON messages data to the specified URL
    conn_messages = http.client.HTTPConnection('192.168.1.85', 5000)
    path_messages = '/ALL_MESSAGES'  # Path for messages
    headers_messages = {'Content-Type': 'application/json'}

    # Send the JSON message counts data to the specified URL
    conn_message_counts = http.client.HTTPConnection('192.168.1.85', 5000)
    path_message_counts = '/CHARACTER_MESSAGE_COUNTS'  # Path for character message counts
    headers_message_counts = {'Content-Type': 'application/json'}

    try:
        # Send data
        conn_data.request('POST', path_data, json_data, headers_data)
        response_data = conn_data.getresponse()
        if response_data.status == 200:
            print(f"Data sent successfully to {conn_data.host}:{conn_data.port}{path_data}")
        else:
            print(f"Error sending data: {response_data.status} - {response_data.reason}")

        # Send messages
        conn_messages.request('POST', path_messages, json_messages, headers_messages)
        response_messages = conn_messages.getresponse()
        if response_messages.status == 200:
            print(f"Messages sent successfully to {conn_messages.host}:{conn_messages.port}{path_messages}")
        else:
            print(f"Error sending messages: {response_messages.status} - {response_messages.reason}")

        # Send message counts
        conn_message_counts.request('POST', path_message_counts, json_message_counts, headers_message_counts)
        response_message_counts = conn_message_counts.getresponse()
        if response_message_counts.status == 200:
            print(f"Message counts sent successfully to {conn_message_counts.host}:{conn_message_counts.port}{path_message_counts}")
        else:
            print(f"Error sending message counts: {response_message_counts.status} - {response_message_counts.reason}")

    except Exception as e:
        print(f"Error sending data or messages: {e}")
    finally:
        conn_data.close()
        conn_messages.close()
        conn_message_counts.close()

    # Wait for 0.1 seconds before the next iteration
    time.sleep(1)
