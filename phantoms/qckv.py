import os
import shutil
import json
from pylinac import StandardImagingQCkV

from util import obj_serializer
import util
import webservice_helper

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
    phantom = StandardImagingQCkV(input_file)
    params = config['analysis_params']
    
    phantom.analyze(low_contrast_threshold=params['low_contrast_threshold'],
                high_contrast_threshold=params['high_contrast_threshold'],
                #invert=False,
                #angle_override=False,
                #center_override=False,
                #size_override=False,
                ssd=params['ssd'],
                low_contrast_method=params['low_contrast_method'],
                visibility_threshold=params['visibility_threshold'],
                #x_adjustment=params['x_adjustment'],
                #y_adjustment=params['y_adjustment'],
                #angle_adjustment=params['angle_adjustment'],
                #roi_size_factor=params['roi_size_factor'],
                #scaling_factor=params['scaling_factor']
    )

    # print results
    log_message(phantom.results())

    file = os.path.join(output_dir, 'analyzed_image.png')
    log_message(f'saving image: {file}')
    phantom.save_analyzed_image(filename=file)

    # copy logo file
    logo_file = config['publish_pdf_params']['logo']
    if not os.path.exists(logo_file):
        # check the current folder
        cwd = util.get_cwd()
        log_file = os.path.join(cwd, log_file)

    if os.path.exists(logo_file):
        log_filename = os.path.basename(logo_file)
        dst = os.path.join(output_dir, log_filename)
        log_message(f'Saving logo file: {dst}')
        shutil.copy(logo_file, dst)
    else:
        log_message('logo_file not found. using default logo image.')
    
    # Save the results as PDF, TXT, and JSON
    result_pdf = os.path.join(output_dir, 'result.pdf')
    log_message(f'Saving result PDF: {result_pdf}')
    params = config['publish_pdf_params']

    phantom.publish_pdf(
        filename=result_pdf,
        notes=notes,
        open_file=True,
        metadata=metadata,    
        logo=params['logo']
    )

    result_txt = os.path.join(output_dir, 'result.txt')
    log_message(f'Saving result TXT: {result_txt}')
    with open(result_txt, 'w') as file:
        file.write(phantom.results())
    
    result = phantom.results_data()
    result_json = os.path.join(output_dir, 'result.json')

    result_dict = json.loads(json.dumps(vars(result), default=obj_serializer))
    result_dict['device_id'] = device_id
    result_dict['performed_by'] = metadata['Performed By']
    result_dict['performed_on'] = metadata['Performed Date']
    result_dict['notes'] =notes 
    result_dict['config'] = config

    log_message(f'Saving result JSON: {result_json}')
    with open(result_json, 'w') as json_file:
        json.dump(result_dict, json_file, indent=4)

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
    url = url = config['webservice_url'] +'/qckvresults'
    res = webservice_helper.post(obj=result_data, url=url)

    if res != None:
        # Assuming the API returns the created document with the _id field
        if '_id' in res:
            document_id = res['_id']
    else:
        raise Exception('Failed posting catphan result!')

    return result_data
'''
