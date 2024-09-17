import matplotlib.pyplot as plt
# Disable interactive mode
plt.ioff()

import argparse

import json
import os
from util import log, obj_serializer, read_json_file
from pylinac import CatPhan604, CatPhan600, CatPhan504, CatPhan503

__version__ = "1.0.0"

# Create the parser
parser = argparse.ArgumentParser(description="CTQA using CatPhans")

# Define the arguments
parser.add_argument("-i", "--input_folder", required=True, help="The path to the folder with input dicom files")
parser.add_argument("-o", "--output_folder", required=False, help="The path to the folder where all the output files will be saved. If not given, the files will be saved to the 'out' folder under the input folder.")
parser.add_argument("-c", "--config_file", required=True, help="Configuration file path")
parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")

# Parse the arguments
args = parser.parse_args()

################
# input_dir
input_dir = args.input_folder
log(f'input_dir={input_dir}')

###############
# output_dir
if not args.output_folder:
    output_dir = os.path.join(input_dir, 'out')
else:
    output_dir = args.output_folder
log(f'output_dir={output_dir}')
if not os.path.exists(output_dir):
    log('outout_dir not found. creating...')
    os.makedirs(output_dir)

##############
#config_file
config_file = args.config_file
log(f'config_file={config_file}')
log(f'loading config file...')
config = read_json_file(config_file)

# result files
result_json = os.path.join(output_dir, 'result.json')
result_pdf = os.path.join(output_dir, 'result.pdf')
result_txt = os.path.join(output_dir, 'result.txt')

catphan_model = config['catphan_model']
log(f'phantom_model={catphan_model}')

log('creating CatPhan604...')
if catphan_model == '604':
    ct = CatPhan604(input_dir)
elif catphan_model == '600':
    ct = CatPhan600(input_dir)
elif catphan_model == '504':
    ct = CatPhan504(input_dir)
elif catphan_model == '503':
    ct = CatPhan503(input_dir)
else:
    log(f'Unknown catphan model: {catphan_model}')

log('analizing...')
params = config['analysis_params']
ct.analyze(
    hu_tolerance=params['hu_tolerance'],
    scaling_tolerance=params['scaling_tolerance'],
    thickness_tolerance=params['thickness_tolerance'],
    low_contrast_tolerance=params['low_contrast_tolerance'],
    cnr_threshold=params['cnr_threshold'],
    zip_after=params['zip_after'],
    contrast_method=params['contrast_method'],
    visibility_threshold=params['visibility_threshold'],
    thickness_slice_straddle=params['thickness_slice_straddle'],
    expected_hu_values=params['expected_hu_values'])

###############
# result_pdf
params = config['publish_pdf_params']
result_pdf = os.path.join(output_dir, params['filename'])
log(f'saving result pdf file, {result_pdf}...')
ct.publish_pdf(filename=result_pdf, 
               notes=params['notes'], 
               open_file=params['open_file'], 
               metadata=params['metadata'], 
               logo=params['logo'] )
############
# result txt
result = ct.results_data()
log(ct.results())
log(f'saving result txt file: {result_txt}...')
with open(result_txt, 'w') as file:
    file.write(ct.results())

##############
# result json
# Convert result object to a dictionary, applying custom serialization
result_dict = json.loads(json.dumps(vars(result), default=obj_serializer))

# Specify the path to save the JSON file
log(f'savin results json file:{result_json}...')
# Save the serialized result to the JSON file
with open(result_json, "w") as json_file:
    json.dump(result_dict, json_file, indent=4)
    
log('done')