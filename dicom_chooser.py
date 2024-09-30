import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk  # For displaying DICOM images as 2D previews

from dicom_helper import parse_dicom_directory, read_dicom_image
import pydicom
from enum import Enum

class SelectionMode(Enum):
    SERIES = 1
    FILE = 2

class DicomChooser:
    def __init__(self, root, input_dir, selection_mode=SelectionMode.SERIES):
        self.root = root
        self.input_dir = input_dir
        self.selected_name = None
        self.selected_files = []
        self.dicom_tree = None  # Store the parsed DICOM structure
        self.tk_image = None  # Store the Tkinter image object
        self.selection_mode = selection_mode

    def show(self):
        # Create a new top-level window
        self.window = tk.Toplevel(self.root)
        
        title = "Select a series" if self.selection_mode==SelectionMode.SERIES else "Select a file"
        self.window.title = title
        # Set the window size and position
        self.window.geometry("800x600")

        # Label for instructions
        # tk.Label(self.series_selection_popup, text="Please select a series or file to preview:").pack(pady=10)

        # Create a treeview to display series under studies and files
        self.series_tree = ttk.Treeview(self.window)
        self.series_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Button to confirm selection
        button_label = "Select Series" if self.selection_mode == SelectionMode.SERIES else 'Select File'
        select_button = tk.Button(self.window, text=button_label, command=self.on_select_clicked)
        select_button.pack(pady=10)

        # Add a frame for image and properties display
        self.image_properties_frame = tk.Frame(self.window, width=800, height=300)
        self.image_properties_frame.pack(fill="both", expand=True)

        # Add a canvas to preview the image
        self.preview_canvas = tk.Canvas(self.image_properties_frame, width=400, height=300)
        self.preview_canvas.pack(side='left')

        # Create a frame for the DICOM properties on the right
        self.properties_frame = tk.Frame(self.image_properties_frame, width=400, height=300)
        self.properties_frame.pack(side="right", fill="both", expand=True)

        # Create a Treeview for displaying DICOM properties
        self.properties_tree = ttk.Treeview(self.properties_frame)
        self.properties_tree.pack(fill="both", expand=True)

        # Define tree columns
        self.properties_tree['columns'] = ('Tag', 'Description', 'Value')
        self.properties_tree.heading('#0', text='', anchor='w')
        self.properties_tree.heading('Tag', text='Tag')
        self.properties_tree.heading('Description', text='Description')
        self.properties_tree.heading('Value', text='Value')
        
        self.properties_tree.column('#0', width=0, stretch=tk.NO)  # Hide default column
        self.properties_tree.column('Tag', anchor='w', width=100)
        self.properties_tree.column('Description', anchor='w', width=150)
        self.properties_tree.column('Value', anchor='w', width=150)

        # Load series into the treeview
        self.load_series_tree()

        # Bind selection event to display preview
        self.series_tree.bind("<<TreeviewSelect>>", self.on_treeview_select)

    def load_series_tree(self):
        # Parse the DICOM files to build the study and series list
        if not self.input_dir:
            messagebox.showerror("Error", "Please select the input folder.")
            return

        self.dicom_tree = parse_dicom_directory(self.input_dir)

        # Populate the treeview with study and series information
        for patient_name, studies in self.dicom_tree.items():
            for study_uid, series_dict in studies.items():
                study_node = self.series_tree.insert('', 'end', text=f"{patient_name} - {study_uid}", open=True)

                # Add series under the study node
                for series_uid, series_data in series_dict.items():
                    modality = series_data.get('modality', 'Unknown')
                    series_datetime = series_data.get('series_datetime', 'Unknown')
                    num_files = len(series_data['files'])
                    # Format series display text to include Modality and DateTime
                    series_display = f"{modality} - {series_datetime} - {series_uid} ({num_files} files)"

                    # Insert the series information as a child node of the study node, with values for lookup
                    series_node = self.series_tree.insert(study_node, 'end', text=series_display, values=(patient_name, study_uid, series_uid))

                    # Add individual DICOM files as children of the series node
                    for dicom_file in series_data['files']:
                        filename = os.path.basename(dicom_file)
                        self.series_tree.insert(series_node, 'end', text=filename, values=(dicom_file,), open=False)

    def on_treeview_select(self, event):
        selected_item = self.series_tree.selection()

        if selected_item:
            # Get the file path if a file is selected
            file_path = self.series_tree.item(selected_item, 'values')[0]

            # If it's a DICOM file, preview the image
            if os.path.isfile(file_path):
                self.preview_dicom_image(file_path)
                self.update_dicom_properties(file_path)

    def update_dicom_properties(self, file_path):
        # Clear the current properties
        for item in self.properties_tree.get_children():
            self.properties_tree.delete(item)

        # Read DICOM file
        dicom_data = pydicom.dcmread(file_path)

        for elem in dicom_data:
            tag = elem.tag
            description = elem.description()
            value = elem.value
            # Insert DICOM element data into the treeview
            self.properties_tree.insert('', 'end', values=(tag, description, str(value)))

    def preview_dicom_image(self, file_path):
        try:
            # Read the DICOM file as a 2D image (utility function needed)
            image = read_dicom_image(file_path)

            # Convert the image for display in Tkinter (assuming grayscale or RGB)
            pil_image = Image.fromarray(image)
            self.tk_image = ImageTk.PhotoImage(pil_image)

            # Clear previous image
            self.preview_canvas.delete("all")

            # Display the image in the canvas
            self.preview_canvas.create_image(200, 150, image=self.tk_image, anchor="center")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load DICOM image: {e}")

    def on_select_clicked(self):
        # Get the selected series node
        selected_items = self.series_tree.selection()
        if not selected_items:
            messagebox.showwarning("Selection", "Please select an item.")
            return

        selected_item = selected_items[0]  # Only considering the first selection

        # Get item values
        item_values = self.series_tree.item(selected_item, 'values')
        
        if self.selection_mode == SelectionMode.SERIES:
            # Ensure the item has both study and series UIDs
            if len(item_values) < 3:
                messagebox.showwarning("Selection", "Invalid selection. Please select a series node.")
                return

            # Retrieve the associated study and series UIDs
            patient_name, study_uid, series_uid = item_values[:3]
        
            # Fetch the actual files for the selected series from the stored DICOM tree
            self.selected_files = self.dicom_tree[patient_name][study_uid][series_uid]['files']

            # Get the label of the selected series
            self.selected_name = self.series_tree.item(selected_item)['text']

        else:
            # selected filename
            selected_item_value = self.series_tree.item(selected_item, 'values')
            self.selected_file = selected_item_value[0]

        # Close the popup window
        self.window.destroy()

    def get_selection(self):
        if self.selection_mode == SelectionMode.SERIES:
            # Returns the selected series name and files
            if self.selected_name is None or not self.selected_files:
                raise ValueError("No series selected.")
            return self.selected_name, self.selected_files
        elif self.selection_mode == SelectionMode.FILE:
            # Returns the selected series name and files
            if self.selected_file is None or not self.selected_file:
                raise ValueError("No file selected.")
            return self.selected_file
        else:
            pass
            

