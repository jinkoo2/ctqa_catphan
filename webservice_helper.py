import json
import re
import requests
from datetime import datetime
import os
import util
import model_helper
import obj_helper

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

def post_analysis_result(result_folder, config, url, log_message):
    
    temp_folder = config['temp_folder']
    
    if not result_folder or not os.path.exists(result_folder):
        raise Exception("The result folder not found.")
    
    # Zip the input folder
    log_message(f"Zipping input folder: {result_folder}")
    zip_filepath = util.zip_folder(result_folder, f'catphan_', temp_folder)
    log_message(f"Result folder zipped at: {zip_filepath}")
    
    # Get the upload URL from config
    zip_upload_url = config['webservice_url'] + '/upload'

    # Upload the zip file to the server
    log_message(f"Uploading zip file: {zip_filepath} to {zip_upload_url}")
    res = upload_zip_file(zip_filepath, zip_upload_url)

    if res != None:
        log_message("Zip file uploaded successfully.")
        log_message(f"Removing zip file....{zip_filepath}")
        os.remove(zip_filepath)

        uploaded_zip_filename = res['fileName']
    else:
        raise Exception("Failed uplaoding zip file!")

    # Ensure the result.json file exists
    result_json = os.path.join(result_folder, 'result.json')

    if not os.path.exists(result_json):
        raise Exception("The result.json file does not exist. Run the analysis first.")

    # Read the result.json file
    with open(result_json, 'r') as json_file:
        result_data = json.load(json_file)

    # add zip filename
    result_data['file'] = uploaded_zip_filename

    # POST the result.json to the API
    res = post(obj=result_data, url=url)

    if res != None:
        # Assuming the API returns the created document with the _id field
        if '_id' in res:
            document_id = res['_id']
    else:
        raise Exception('Failed posting catphan result!')

    return result_data

def post_result_as_measurement1ds(result_data, app, site_id, device_id, phantom_id, url, log):
    # travese the result object and collect numbers
    log('collecting numbers from the result file...')
    kvps = obj_helper.traverse_and_collect_numbers(result_data)

    # convert the numbers key value pairs to measurement objects
    log('converting numbers kvps to measurement1d objects...')
    measurements = model_helper.convert_kvps_to_measurement1d(key_value_pairs=kvps, 
                                                            key_prefix=f'{phantom_id.lower()}_',
                                                            device_id=f'{site_id}|{device_id}', 
                                                            app=app)

    log(f'posting the measurement1d array to the server... url={url}')
    res = post(measurements, url=url)
    if res != None:
        log("Post succeeded!")
        return res
    else:
        log("Post failed!")
        return None
        
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
