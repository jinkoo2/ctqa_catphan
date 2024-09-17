from datetime import datetime, date
import json

def log(str):
    print(str)


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