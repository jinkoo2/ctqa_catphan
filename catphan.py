import os
import shutil
import json
from pylinac import CatPhan604, CatPhan600, CatPhan504, CatPhan503
from util import obj_serializer
import util
import webservice_helper

def run_analysis(device_id, input_dir, output_dir, config, notes, metadata, log_message):

    if not input_dir:
        log_message("Error: Please select the input folder.")
        return

    if not output_dir:
        output_dir = os.path.join(input_dir, 'out')

    log_message(f'Input directory: {input_dir}')
    log_message(f'Output directory: {output_dir}')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Catphan analysis logic
    catphan_model = config['catphan_model']
    log_message(f'Phantom model: {catphan_model}')
    
    if catphan_model == '604':
        ct = CatPhan604(input_dir)
    elif catphan_model == '600':
        ct = CatPhan600(input_dir)
    elif catphan_model == '504':
        ct = CatPhan504(input_dir)
    elif catphan_model == '503':
        ct = CatPhan503(input_dir)
    else:
        log_message(f'Error:Unknown CatPhan model: {catphan_model}!')
        return
    
    log_message('Running analysis...')
    params = config['analysis_params']
    ct.analyze(
        hu_tolerance=params['hu_tolerance'],
        scaling_tolerance=params['scaling_tolerance'],
        thickness_tolerance=params['thickness_tolerance'],
        low_contrast_tolerance=params['low_contrast_tolerance'],
        cnr_threshold=params['cnr_threshold'],
        zip_after=False,
        contrast_method=params['contrast_method'],
        visibility_threshold=params['visibility_threshold'],
        thickness_slice_straddle=params['thickness_slice_straddle'],
        expected_hu_values=params['expected_hu_values']
    )

    # print results
    log_message(ct.results())

    file = os.path.join(output_dir, 'analyzed_image.png')
    log_message(f'saving image: {file}')
    ct.save_analyzed_image(filename=file)
    
    sub_image_header = os.path.join(output_dir, 'analyzed_subimage')
    #* ``hu`` draws the HU linearity image.
    #* ``un`` draws the HU uniformity image.
    #* ``sp`` draws the Spatial Resolution image.
    #* ``lc`` draws the Low Contrast image (if applicable).
    #* ``mtf`` draws the RMTF plot.
    #* ``lin`` draws the HU linearity values. Used with ``delta``.
    #* ``prof`` draws the HU uniformity profiles.
    #* ``side`` draws the side view of the phantom with lines of the module locations.
    sub_image_list = ['hu', 'un', 'sp', 'lc', 'mtf', 'lin', 'prof', 'side']
    for sub in sub_image_list:
        try:
            dst = f'{sub_image_header}.{sub}.png'
            log_message(f'saving sub image: {dst}')
            ct.save_analyzed_subimage(filename=dst, subimage=sub)
        except:
            pass

    # copy logo file
    logo_file = config['publish_pdf_params']['logo']
    if os.path.exists(logo_file):
        log_filename = os.path.basename(logo_file)
        dst = os.path.join(output_dir, log_filename)
        log_message(f'Saving logo file: {dst}')
        shutil.copy(logo_file, dst)
    else:
        log_message('logo_file not found. using default logo image.')
    
    # Save the results as PDF, TXT, and JSON
    result_pdf = os.path.join(output_dir, config['publish_pdf_params']['filename'])
    log_message(f'Saving result PDF: {result_pdf}')
    params = config['publish_pdf_params']

    ct.publish_pdf(
        filename=result_pdf,
        notes=notes,
        open_file=True,
        metadata=metadata,    
        logo=params['logo']
    )

    result_txt = os.path.join(output_dir, 'result.txt')
    log_message(f'Saving result TXT: {result_txt}')
    with open(result_txt, 'w') as file:
        file.write(ct.results())
    
    result = ct.results_data()
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

def push_to_server(result_folder, config, log_message):
    
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
    url = url = config['webservice_url'] +'/catphanresults'
    res = webservice_helper.post(obj=result_data, url=url)

    if res != None:
        # Assuming the API returns the created document with the _id field
        if '_id' in res:
            document_id = res['_id']
    else:
        raise Exception('Failed posting catphan result!')

    return result_data

