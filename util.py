from datetime import datetime, date
import json
import sys
import os
import zipfile

def log(str):
    print(str)

def get_app_name():
    # Get the full path of the script or executable
    exe_full_path = sys.argv[0]

    # Extract the base name (file name or exe name) and remove the extension
    exe_name = os.path.splitext(os.path.basename(exe_full_path))[0]

    return exe_name

def get_cwd():
    if getattr(sys, 'frozen', False):
        # If running as a compiled executable
        current_folder = os.path.dirname(sys.executable)
    else:
        # If running as a script
        current_folder = os.path.dirname(os.path.abspath(__file__))
    
    return current_folder


# convert to dict
# Using vars() will fail if there are complex types, so we'll handle that
def obj_serializer(obj):
    """Custom JSON serializer for objects not serializable by default."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()  # Convert datetime objects to ISO format
    elif hasattr(obj, "__dict__"):
        # For complex objects, recursively convert their __dict__ attributes
        return vars(obj)
    else:
        return str(obj)  # Convert anything else to a string

def read_json_file(json_file_path):
    # Open and read the JSON file
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)

    return data

def zip_folder(folder_path, filename_prefix, output_folder_path):
    # Generate a zip file name based on timestamp
    zip_filename = f"{filename_prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_filepath = os.path.join(output_folder_path, zip_filename)
    
    # Create the zip file
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Traverse all files and directories within the input folder
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Create the full file path
                file_path = os.path.join(root, file)
                # Write the file to the zip archive with a relative path
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
                
    return zip_filepath

def datetime_to_string_yyyymmdd_hhmmss(dt):
    return dt.strftime('%Y%m%d_%H%M%S')