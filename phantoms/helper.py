import os
import shutil
import util 
import json
from util import obj_serializer
import obj_helper

def copy_logo(config, output_dir, log_message):
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

def save_result_as_pdf(phantom, output_dir, config, notes, metadata, log_message ):
    # Save the results as PDF, TXT, and JSON
    result_pdf = os.path.join(output_dir, 'result.pdf')
    log_message(f'Saving result PDF: {result_pdf}')
    params = config['publish_pdf_params']

    open_file = params['open_file']

    phantom.publish_pdf(
        filename=result_pdf,
        notes=notes,
        open_file=open_file,
        metadata=metadata,    
        logo=params['logo']
    )

def save_result_as_txt(phantom, output_dir, log_message):
    result_txt = os.path.join(output_dir, 'result.txt')
    log_message(f'Saving result TXT: {result_txt}')
    with open(result_txt, 'w') as file:
        file.write(phantom.results())

def save_result_as_json(phantom, output_dir, device_id, notes, config, metadata, log_message ):
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

def write_line(file, line):
    with open(file, 'w') as file:
        file.write(f'{line}\n')

def append_line(file, line):
    with open(file, 'a') as file:
        file.write(f'{line}\n')


def append_result_to_phantom_csv(phantom, output_dir, device_id, notes, metadata, log_message ):

    # result
    result_json = os.path.join(output_dir, 'result.json')

    if not os.path.exists(result_json):
        raise Exception("The result.json file does not exist. Run the analysis first.")

    # Read the result.json file
    with open(result_json, 'r') as json_file:
        result_data = json.load(json_file)

    log_message('collecting perperties from the result file...')
    kvps = obj_helper.traverse_and_collect_numbers_strings(result_data)
    
    # header
    keys = [item['key'] for item in kvps]
    header = ','.join(keys)

    # line
    values = [str(item['value']).replace(',', '[comma]').replace('\n', '[newline]') for item in kvps]
    line = ','.join(values)

    # csv_file
    parent_dir = os.path.dirname(output_dir)
    csv_file = os.path.join(parent_dir, 'results.csv')

    log_message(f'csv_file={csv_file}')

    if not os.path.exists(csv_file):
        log_message('csv file not found. creating and adding the header...')
        write_line(csv_file, header)
    
    log_message('appending a result line to csv file')
    append_line(file=csv_file, line=line)
