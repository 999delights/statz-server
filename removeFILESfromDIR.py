import os

def delete_dds_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".dds"):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {str(e)}")

if __name__ == "__main__":
    root_directory = r'C:\Users\andre\Downloads\Media\interface'
    delete_dds_files(root_directory)
