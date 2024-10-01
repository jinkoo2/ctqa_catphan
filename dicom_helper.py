# util.py
import os
import pydicom
import numpy as np
from datetime import datetime

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

def get_acquisition_datetime(dicom_file_path):
    # Read the DICOM file
    dicom_data = pydicom.dcmread(dicom_file_path)

    # Extract the acquisition date and time
    acquisition_date = dicom_data.get('AcquisitionDate', None)
    acquisition_time = dicom_data.get('AcquisitionTime', None)

    if acquisition_date and acquisition_time:
        # Pad the time string to ensure it is always 6 characters long (HHMMSS)
        acquisition_time = acquisition_time[:6].ljust(6, '0')

        # Combine date and time into a datetime object
        date_time_str = acquisition_date + acquisition_time
        acquisition_datetime = datetime.strptime(date_time_str, "%Y%m%d%H%M%S")
        
        print("Acquisition DateTime:", acquisition_datetime)
        return acquisition_datetime
    else:
        raise Exception("Acquisition Date or Time not found in the DICOM file.")

def get_acquisition_datetime_str(dicom_file_path):
    # Get the datetime object
    dt = get_acquisition_datetime(dicom_file_path)
    
    # Return formatted string 'yyyyMMdd_HHmmss'
    return dt.strftime('%Y%m%d_%H%M%S')

def get_study_datetime(dicom_file_path):
    # Read the DICOM file
    dicom_data = pydicom.dcmread(dicom_file_path)

    # Extract the study date and time
    study_date = dicom_data.get('StudyDate', None)
    study_time = dicom_data.get('StudyTime', None)

    if study_date and study_time:
        # Pad the study time to ensure it's always 6 characters long (HHMMSS)
        study_time = study_time[:6].ljust(6, '0')

        # Combine date and time into a datetime object
        datetime_str = study_date + study_time
        study_datetime = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
        
        return study_datetime
    else:
        raise Exception("Study Date or Time not found in the DICOM file.")

def get_study_datetime_str(dicom_file_path):
    # Get the datetime object
    dt = get_study_datetime(dicom_file_path)
    
    # Return formatted string 'yyyyMMdd_HHmmss'
    return dt.strftime('%Y%m%d_%H%M%S')