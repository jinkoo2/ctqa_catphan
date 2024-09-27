# util.py
import os
import pydicom
import numpy as np

def parse_dicom_directory(directory, include_subfolders=False):
    dicom_tree = {}

    # Determine the function to use for traversing the directory
    if include_subfolders:
        # Traverse through the directory and all its subdirectories for DICOM files
        directory_iterator = os.walk(directory)
    else:
        # Only list files in the specified directory (no subdirectories)
        directory_iterator = [(directory, [], os.listdir(directory))]

    for root, _, files in directory_iterator:
        for file in files:
            file_path = os.path.join(root, file)

            try:
                # Read the DICOM file
                ds = pydicom.dcmread(file_path, stop_before_pixels=True)

                # Extract required information
                patient_name = f'{ds.PatientName}'  # Convert to string
                study_uid = f'{ds.StudyInstanceUID}'
                series_uid = f'{ds.SeriesInstanceUID}'
                modality = f'{ds.Modality}'
                series_date = f"{ds.get('SeriesDate', 'Unknown')}"  # Get SeriesDate or set as 'Unknown' if not available
                series_time = f"{ds.get('SeriesTime', 'Unknown')}"  # Get SeriesTime or set as 'Unknown' if not available

                # Combine date and time for the label
                series_datetime = f"{series_date} {series_time}"

                # Organize files by patient, study, and series
                if patient_name not in dicom_tree:
                    dicom_tree[patient_name] = {}
                if study_uid not in dicom_tree[patient_name]:
                    dicom_tree[patient_name][study_uid] = {}
                if series_uid not in dicom_tree[patient_name][study_uid]:
                    dicom_tree[patient_name][study_uid][series_uid] = {
                        'files': [], 
                        'modality': modality, 
                        'series_datetime': series_datetime
                    }

                dicom_tree[patient_name][study_uid][series_uid]['files'].append(file_path)

            except Exception as e:
                print(f"Error reading DICOM file {file_path}: {e}")
                continue

    return dicom_tree
def read_dicom_image(file_path):
    # Read the DICOM file
    dicom_data = pydicom.dcmread(file_path)

    return get_dicom_image(dicom_data)

def get_dicom_image(dicom_data):
    
    # Extract pixel data and apply any necessary transformations
    image_array = dicom_data.pixel_array

    # Optionally, normalize or convert to grayscale/RGB if needed
    # For example, normalize to 0-255 for 8-bit display
    image_array = (image_array - np.min(image_array)) / (np.max(image_array) - np.min(image_array)) * 255
    image_array = image_array.astype(np.uint8)

    return image_array
