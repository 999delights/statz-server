import os

# Replace 'your_image_folder_path' with the path to your folder containing images
folder_path = r'C:\Users\andre\AppData\Local\Programs\phBot Testing\minimap'

# List all the files in the folder
file_names = os.listdir(folder_path)

# Specify the name of the output file
output_file = 'image_names.txt'

# Write the file names to the output file
with open(output_file, 'w') as f:
    for file_name in file_names:
        f.write(file_name + '\n')

print(f"File names have been exported to {output_file}")
