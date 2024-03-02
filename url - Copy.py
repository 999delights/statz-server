import os

# Images directory path and name
image_directory = 'C:\\Users\\andre\\OneDrive\\Desktop\\silkroad-laravel-master\\skill'

# Iterate through each image file in the specified directory
for root, _, files in os.walk(image_directory):
    for image_name in files:
        # Split the filename into base and extension
        base, ext = os.path.splitext(image_name)
        # Split the base name into parts using underscores
        parts = base.split('_')
        # Remove the last part (everything after the last underscore)
        new_base = '_'.join(parts[:-1])
        # Create the new filename by adding back the PNG extension
        new_filename = new_base + '.png'
        old_path = os.path.join(root, image_name)
        new_path = os.path.join(root, new_filename)

        # Check if the new filename already exists before renaming
        if not os.path.exists(new_path):
            os.rename(old_path, new_path)

print("Image files have been renamed and converted to PNG.")
