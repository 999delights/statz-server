import re
import ast
import json

# Read the data from npcdata.txt
with open('npcdata.txt', 'r') as file:
    data = file.read()

# Remove unnecessary characters and keep only the JSON-like portion
data = re.search(r'var TPs=(\[.*\])', data, re.DOTALL).group(1)

# Convert the JSON-like string into a Python list
npcs_list = ast.literal_eval(data)

# Create a dictionary to store the consolidated data
npcs_dict = {}

# Group NPCs by region
for npc in npcs_list:
    region = npc['region']
    if region in npcs_dict:
        npcs_dict[region].append(npc)
    else:
        npcs_dict[region] = [npc]

# Define the output JSON file path
output_file = 'tp_data.json'

# Write the dictionary as JSON to the output file
with open(output_file, 'w') as json_file:
    json.dump(npcs_dict, json_file, indent=4)

print(f"Data has been successfully converted to {output_file}.")
