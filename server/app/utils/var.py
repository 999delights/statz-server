# config.py
main_directory_path = None
manager_exe_path = None
silkroad_launcher_path = None


info_path = count_path = config_path = ""
statz_path = chat_path = stall_path = events_path = ""
live_chat_path= tasks_path = speed_path = ""



# Initialize empty dictionaries to temporarily store the gathered data before sending.
statz_data = {}
chat_data = {}
events_data = {}
speed_data = {}
new_chat_saved = False

speed_pause = False
events_sent = False