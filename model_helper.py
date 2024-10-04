from datetime import datetime

# Convert the key-value pairs into Number1D objects
def convert_kvps_to_number1d_or_stirng1d_list(key_value_pairs, key_prefix, device_id, app):
    numbers = []
    current_time = datetime.now().isoformat()  # Current time for the `time` field

    for pair in key_value_pairs:
        number = {
            'device_id': device_id,
            'series_id': f'{key_prefix}{pair['key']}',   # Map key to series_id
            'value': pair['value'],     # Map value to value
            'time': current_time,       # Set time to current time
            'notes': '',                # Empty notes field
            'by': '',                   # Empty 'by' field
            'app': app  # App name and version
        }
        numbers.append(number)
    
    return numbers
