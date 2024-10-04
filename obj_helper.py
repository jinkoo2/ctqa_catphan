import json
import re

def python_compatible_key(key):
    # Replace non-alphanumeric characters and spaces with underscores
    return re.sub(r'[^a-zA-Z0-9_]', '_', key)

def traverse_and_collect_numbers(obj, parent_key='', result=None):
    if result is None:
        result = []

    for key, value in obj.items():
        full_key = f"{parent_key}_{key}" if parent_key else key
        full_key = python_compatible_key(full_key)

        if isinstance(value, (int, float)):  # Check if the value is a number
            result.append({'key': full_key, 'value': value})
        elif isinstance(value, dict):  # Recursively traverse dictionaries
            traverse_and_collect_numbers(value, full_key, result)

    return  sorted(result, key=lambda x: x['key'])

def traverse_and_collect_strings(obj, parent_key='', result=None):
    if result is None:
        result = []

    for key, value in obj.items():
        full_key = f"{parent_key}_{key}" if parent_key else key
        full_key = python_compatible_key(full_key)

        if isinstance(value, str):  # Check if the value is a string
            result.append({'key': full_key, 'value': value})
        elif isinstance(value, dict):  # Recursively traverse dictionaries
            traverse_and_collect_strings(value, full_key, result)

    return  sorted(result, key=lambda x: x['key'])

def traverse_and_collect_numbers_strings(obj, parent_key='', result=None):
    if result is None:
        result = []

    for key, value in obj.items():
        full_key = f"{parent_key}_{key}" if parent_key else key
        full_key = python_compatible_key(full_key)

        if isinstance(value, (int, float, str)):  # Check if the value is a number
            result.append({'key': full_key, 'value': value})
        elif isinstance(value, dict):  # Recursively traverse dictionaries
            traverse_and_collect_numbers_strings(value, full_key, result)

    return  sorted(result, key=lambda x: x['key'])


if __name__ == '__main__':
    # Example usage with a result.json object
    result_json = {
        "measurement": {
            "temperature": 25.4,
            "pressure": 101.3,
            "details": {
                "humidity": 60,
                "altitude": 300.2,
                "location_name": "Room A",
                "complex_data": {
                    "value-1": 42.0,
                    "value 2": 19.5,
                    "Value!": 37
                }
            }
        }
    }

    # Traverse the result.json and collect the key-value pairs
    key_value_pairs = traverse_and_collect(result_json)

    # Print the result
    for pair in key_value_pairs:
        print(pair)
