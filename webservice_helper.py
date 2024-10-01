import json
import re
import requests
from datetime import datetime
import os

# Post the Measurement1D array to the API
def post_measurements(measurements, url):
    headers = {'Content-Type': 'application/json'}

    # Send a POST request
    response = requests.post(url, json=measurements, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200 or response.status_code == 201:
        print("Measurements successfully posted.")
        return response.json()
    else:
        print(f"Failed to post measurements: {response.status_code} - {response.text}")
        return None
 
def post(obj, url):
    # POST the result.json to the API
    headers = {'Content-Type': 'application/json'}

    print(f'Sending result.json to {url}...')
    response = requests.post(url, json=obj, headers=headers)

    # Check if the request was successful
    if response.status_code in [200, 201]:
        print("Record successfully sent to the server.")
        return response.json()
    else:
        print(f"Failed to send record: {response.status_code} - {response.text}")
        return None

def upload_zip_file(filepath, url):
    try:
        # Open the zip file in binary mode
        with open(filepath, 'rb') as file:
            # Create a dictionary for the file to upload
            files = {'file': (os.path.basename(filepath), file, 'application/zip')}
            
            # Make a POST request to upload the file
            response = requests.post(url, files=files)

            # Check the response status code
            if response.status_code in (200, 201):
                print(f"File {filepath} uploaded successfully.")
                return response.json()
            else:
                print(f"Failed to upload file: {response.status_code} - {response.text}")
                return None
        
    except Exception as e:
        print(f"Error while uploading zip file: {e}")

if __name__ == '__main__':
    # Example usage with a result.json object
    result_json = {
        "measurement": {
            "temperature": 25.4,
            "pressure": 101.3,
            "details": {
                "humidity": 60,
                "altitude": 300.2,
                "complex_data": {
                    "value-1": 42.0,
                    "value 2": 19.5,
                    "Value!": 37
                }
            }
        }
    }

    # Step 1: Traverse the result.json and collect the key-value pairs
    key_value_pairs = traverse_and_collect(result_json)

    # Step 2: Convert the key-value pairs to Measurement1D objects
    measurement1d_objects = convert_to_measurement1d(key_value_pairs)

    # Step 3: Post the Measurement1D objects to the web service
    post_measurements(measurement1d_objects)
