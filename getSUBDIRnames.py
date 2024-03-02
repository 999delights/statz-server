import os

# Define the folder path
folder_path = r'C:\Users\andre\Downloads\Media\icon'

# Initialize an empty list to store relative paths
relative_paths = []

# Walk through the directory tree and collect relative paths
for root, dirs, files in os.walk(folder_path):
    for dir_name in dirs:
        # Get the relative path of the subdirectory
        relative_path = os.path.relpath(os.path.join(root, dir_name), folder_path)
        # Replace backslashes with forward slashes
        relative_path = relative_path.replace('\\', '/')
        relative_paths.append(relative_path)

# Specify the name of the output file
output_file = 'subdirectories.txt'

# Write the relative paths to the output file
with open(output_file, 'w') as f:
    for path in relative_paths:
        f.write(path + '\n')

print(f"Subdirectories have been saved to {output_file}")
