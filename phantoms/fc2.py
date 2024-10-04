import os
import shutil
import json
from pylinac import StandardImagingFC2

from util import obj_serializer
import util
import webservice_helper
import phantoms.helper

def run_analysis(device_id, input_file, output_dir, config, notes, metadata, log_message):

    if not input_file:
        raise Exception(f"input_file not valid - {input_file}")

    if not os.path.exists(input_file):
        raise Exception(f"input_file not found - {input_file}")

    if not output_dir:
        raise Exception(f"output_dir not valid - {output_dir}")

    log_message(f'Input File: {input_file}')
    log_message(f'Output directory: {output_dir}')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Catphan analysis logic
    log_message('Running analysis...')
    phantom = StandardImagingFC2(input_file)
    params = config['analysis_params']
    
    phantom.analyze(
        invert=False,
        fwxm=params['fwxm'],
        bb_edge_threshold_mm=params['bb_edge_threshold_mm']
    )

    # print results
    log_message(phantom.results())

    file = os.path.join(output_dir, 'analyzed_image.png')
    log_message(f'saving image: {file}')
    phantom.save_analyzed_image(filename=file)

    phantoms.helper.copy_logo(config=config, output_dir=output_dir, log_message=log_message)
    
    phantoms.helper.save_result_as_pdf(phantom=phantom, output_dir=output_dir, config=config, notes=notes, metadata=metadata, log_message=log_message)

    phantoms.helper.save_result_as_txt(phantom=phantom, output_dir=output_dir, log_message=log_message)
    
    phantoms.helper.save_result_as_json(phantom=phantom, output_dir=output_dir, device_id=device_id, notes=notes, config=config, metadata=metadata, log_message=log_message)
    
    phantoms.helper.append_result_to_phantom_csv(phantom=phantom, output_dir=output_dir, device_id=device_id, notes=notes, metadata=metadata, log_message=log_message)


    log_message('Analysis completed.')
'''
def push_to_server(result_folder, config, log_message):
    
    temp_folder = config['temp_folder']
    
    if not result_folder or not os.path.exists(result_folder):
        raise Exception("The result folder not found.")
    
    # Zip the input folder
    log_message(f"Zipping input folder: {result_folder}")
    zip_filepath = util.zip_folder(result_folder, f'analysis_', temp_folder)
    log_message(f"Result folder zipped at: {zip_filepath}")
    
    # Get the upload URL from config
    zip_upload_url = config['webservice_url'] + '/upload'

    # Upload the zip file to the server
    log_message(f"Uploading zip file: {zip_filepath} to {zip_upload_url}")
    res = webservice_helper.upload_zip_file(zip_filepath, zip_upload_url)

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
    url = url = config['webservice_url'] +'/fc2results'
    res = webservice_helper.post(obj=result_data, url=url)

    if res != None:
        # Assuming the API returns the created document with the _id field
        if '_id' in res:
            document_id = res['_id']
    else:
        raise Exception('Failed posting catphan result!')

    return result_data
'''
