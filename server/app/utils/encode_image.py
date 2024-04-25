import base64
import os

def encode_image_to_base64(path):
    """Encode image file to base64 string."""
    print(path)
    # Normalize path to correct any OS-specific variations
    normalized_path = os.path.normpath(path)
    print(normalized_path)
    
    try:
        with open(normalized_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_image
    except FileNotFoundError:
        print(f"File not found: {normalized_path}")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
