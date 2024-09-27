import os
import tkinter as tk
from tkinter import ttk
import pydicom

class DicomViewer:
    def __init__(self, root, file_path):
        self.root = root
        self.file_path = file_path
        
        self.setup_ui()

    def setup_ui(self):
        # Set up main window
        self.root.title("DICOM Viewer")
        self.root.geometry("800x600")
        
        # Create a frame for the image preview on the left
        self.image_frame = tk.Frame(self.root, width=400, height=600, bg="black")
        self.image_frame.pack(side="left", fill="both", expand=True)
        
        # Create a canvas for the DICOM image
        self.image_canvas = tk.Canvas(self.image_frame, bg="black")
        self.image_canvas.pack(fill="both", expand=True)
        
        # Create a frame for the DICOM properties on the right
        self.properties_frame = tk.Frame(self.root, width=400, height=600)
        self.properties_frame.pack(side="right", fill="both", expand=True)
        
        # Create a Treeview for displaying DICOM properties
        self.dicom_tree = ttk.Treeview(self.properties_frame)
        self.dicom_tree.pack(fill="both", expand=True)

        # Define tree columns
        self.dicom_tree['columns'] = ('Tag', 'Description', 'Value')
        self.dicom_tree.heading('#0', text='', anchor='w')
        self.dicom_tree.heading('Tag', text='Tag')
        self.dicom_tree.heading('Description', text='Description')
        self.dicom_tree.heading('Value', text='Value')
        
        self.dicom_tree.column('#0', width=0, stretch=tk.NO)  # Hide default column
        self.dicom_tree.column('Tag', anchor='w', width=100)
        self.dicom_tree.column('Description', anchor='w', width=150)
        self.dicom_tree.column('Value', anchor='w', width=150)

        # Load and display DICOM information
        self.load_dicom()

    def load_dicom(self):
        # Read the DICOM file
        dicom_data = pydicom.dcmread(self.file_path)

        # Display DICOM image on the canvas
        self.display_image(dicom_data)

        # Display DICOM metadata in the treeview
        self.display_metadata(dicom_data)

    def display_image(self, dicom_data):
        # Process DICOM pixel data to display it in the canvas
        # This part can be expanded to handle image scaling, grayscale conversion, etc.
        pass  # Placeholder for displaying the image

    def display_metadata(self, dicom_data):
        # Iterate over DICOM metadata elements
        for elem in dicom_data:
            tag = elem.tag
            description = elem.description()
            value = elem.value
            # Insert DICOM element data into the treeview
            self.dicom_tree.insert('', 'end', values=(tag, description, value))

# Usage Example
if __name__ == "__main__":
    root = tk.Tk()
    viewer = DicomViewer(root, "D:\\Temp\\image qa\\kv\\fc2.dcm")  # Replace with actual file path
    root.mainloop()
