import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry  # Date picker widget
from tkinter import ttk  # For progress bar
import threading
import time
from util import read_json_file

import obj_helper
import util
import model_helper
import webservice_helper

from dicom_chooser import DicomChooser, SelectionMode

SETTINGS_FILE = 'settings.json'

# Splash Screen
def show_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)  # Hide window borders and controls
    splash.geometry("300x200+500+300")  # Set the position and size of the splash screen
    splash_label = tk.Label(splash, text="Loading CT QA App...", font=("Helvetica", 16))
    splash_label.pack(expand=True)
    splash.update()
    time.sleep(2)  # Simulate some loading time (2 seconds)
    splash.destroy()  # Close the splash screen

def find_obj_of_id(objs, id):
    for obj in objs:
        if obj["id"] == id:
            return obj

def get_obj_id_list(objs):
    return [obj["id"] for obj in objs]
                  
class CTQAGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CTQA-CatPhans")

        # Set the application icon (ensure app.ico is in the same directory as this script)
        self.root.iconbitmap('app.ico')

        # Load saved settings
        self.settings = self.load_settings()
        self.config = self.load_config()
    
        # Site, Device, and Phantom Selection Comboboxes
        self.selection_frame = tk.Frame(root)
        self.selection_frame.pack(pady=5, padx=5, fill="x")

        # Site selection
        tk.Label(self.selection_frame, text="Site:").pack(side="left", padx=5)
        
        sites = self.config["sites"]
        site_ids = get_obj_id_list(sites)
        self.site_combobox = ttk.Combobox(self.selection_frame, values=site_ids)
        self.site_combobox.pack(side="left", fill="x", expand=True)
        self.site_combobox.bind('<<ComboboxSelected>>', self.on_site_combobox_changed)

        # Device selection
        tk.Label(self.selection_frame, text="Device:").pack(side="left", padx=5)
        self.device_combobox = ttk.Combobox(self.selection_frame, values=[""])
        self.device_combobox.pack(side="left", fill="x", expand=True)

        # Phantom selection
        tk.Label(self.selection_frame, text="Phantom:").pack(side="left", padx=5)
        phantoms = self.config.get('phantoms', [])
        self.phantom_combobox = ttk.Combobox(self.selection_frame, values=get_obj_id_list(phantoms))
        self.phantom_combobox.pack(side="left", fill="x", expand=True)

        # Set default selections from settings if available
        self.site_combobox.set(self.settings.get('site', ''))
        self.on_site_combobox_changed({})
        self.device_combobox.set(self.settings.get('device', ''))
        self.phantom_combobox.set(self.settings.get('phantom', ''))

        # Add Performed By Dropdown (Combobox) and Performed Date Entry
        self.user_frame = tk.Frame(root)
        self.user_frame.pack(pady=5, padx=5, fill="x")

        # Performed By Label and Combobox
        self.performed_by_label = tk.Label(self.user_frame, text="Performed By:")
        self.performed_by_label.pack(side="left", padx=5)
        self.performed_by_combobox = ttk.Combobox(self.user_frame)
        self.performed_by_combobox.pack(side="left", fill="x", expand=True)

        # Performed Date Label and Entry
        self.date_frame = tk.Frame(root)
        self.date_frame.pack(pady=5, padx=5, fill="x")

        self.performed_date_label = tk.Label(self.date_frame, text="Performed Date:")
        self.performed_date_label.pack(side="left", padx=5)

        # Date picker (DateEntry) allowing both selection and manual entry
        self.performed_date_entry = DateEntry(self.date_frame, selectmode='day', date_pattern='y-mm-dd')
        self.performed_date_entry.pack(side="left", fill="x", expand=True)

        # Input folder frame (button + label)
        self.input_frame = tk.Frame(root)
        self.input_frame.pack(pady=5, padx=5, fill="x")
        
        self.input_folder_button = tk.Button(self.input_frame, text="Select Input Folder", command=self.select_input_folder)
        self.input_folder_button.pack(side="left", padx=5)
        self.input_folder_path = tk.Label(self.input_frame, text=self.settings.get('input_folder', ''), relief=tk.SUNKEN, anchor="w")
        self.input_folder_path.pack(side="left", fill="x", expand=True)

        # Output folder frame (button + label)
        self.output_frame = tk.Frame(root)
        self.output_frame.pack(pady=5, padx=5, fill="x")
        
        self.output_folder_button = tk.Button(self.output_frame, text="Output Folder", command=self.select_output_folder)
        self.output_folder_button.pack(side="left", padx=5)
        self.output_folder_button.config(state=tk.DISABLED, relief="flat", borderwidth=0, fg="black")
        self.output_folder_path = tk.Label(self.output_frame, text=self.settings.get('output_folder', ''), relief=tk.SUNKEN, anchor="w")
        self.output_folder_path.pack(side="left", fill="x", expand=True)

        # Notes Section
        self.notes_frame = tk.Frame(root)
        self.notes_frame.pack(pady=5, padx=5, fill="x")

        self.notes_label = tk.Label(self.notes_frame, text="Notes:")
        self.notes_label.pack(side="top", anchor="w")

        self.notes_text = tk.Text(self.notes_frame, height=3, wrap="word")
        self.notes_text.pack(fill="x", padx=5, pady=5)

        # Create "Run Analysis" button
        self.run_button = tk.Button(root, text="Run Analysis", command=self.run_analysis_thread)
        self.run_button.pack(pady=10)

        # Create "Record" button
        self.push_to_server_button = tk.Button(root, text="Push to server", command=self.record_result_thread)
        self.push_to_server_button.pack(pady=10)
       
        # Create a frame to hold the Text widget and the Scrollbar for log output
        self.log_frame = tk.Frame(root)
        self.log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create a Scrollbar
        self.scrollbar = tk.Scrollbar(self.log_frame)
        self.scrollbar.pack(side="right", fill="y")

        # Create the Text widget for logging messages
        self.log_output = tk.Text(self.log_frame, wrap="word", yscrollcommand=self.scrollbar.set)
        self.log_output.pack(side="left", fill="both", expand=True)

        # Configure the Scrollbar to work with the Text widget
        self.scrollbar.config(command=self.log_output.yview)

        # Progress bar and status label at the bottom of the window
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack(side="bottom", pady=5)
        self.progress_bar = ttk.Progressbar(root, mode="indeterminate")
        self.progress_bar.pack(side="bottom", fill="x", padx=5, pady=5)

        # Set up the exit event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # after all UIs created:
        self.populate_performed_by()  # Populate the combobox with data from config file
        # Set the default value from the loaded settings, if available
        performed_by = self.settings.get('performed_by', '')
        if performed_by:
            self.performed_by_combobox.set(performed_by)



    def on_site_combobox_changed(self, event):
        selected_value = self.site_combobox.get()
        print(f"Selected value: {selected_value}")

        if selected_value==None or selected_value=="":
            self.device_combobox.set('')
            self.device_combobox['values']=()
            return 
        
        sites = self.config.get('sites', [])

        site = find_obj_of_id(sites, selected_value)        
        if site == None:
            self.log_message("site not found in the configuration file.")
            return 
        
        devices = site["devices"]
        device_ids = get_obj_id_list(devices)

        self.device_combobox['values'] = device_ids
        self.device_combobox.set('')

    def load_config(self):
        # config file path
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        config_file = os.path.join(current_dir, 'config.json')

        if not os.path.exists(config_file):
            messagebox.showerror("Config file not found. It should be in the same folder of this executablel file")
            return

        return read_json_file(config_file)

    def site(self):
        if self.site_combobox.get() == "":
            raise Exception("Please select a site!")
            
        return self.site_combobox.get().strip()
    
    def device(self):
        if self.device_combobox.get() == "":
            raise Exception("Please select a device!")
            
        return self.device_combobox.get().strip()
    
    def device_id(self):
        return f'{self.site()}|{self.device()}'
    
    def phantom(self):
        if self.phantom_combobox.get() == "":
            raise Exception("Please select a phantom!")

        return self.phantom_combobox.get().strip()
    

    def load_phantom_config(self):
        # config file path
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        site = self.site().lower()
        device = self.device().lower()
        phantom = self.phantom().lower()

        config_file = os.path.join(current_dir, f'config.{site}.{device}.{phantom}.json')

        if not os.path.exists(config_file):
            raise Exception(f"Error:Phantom config file not found. {config_file}")
            return

        return read_json_file(config_file)
    
    def populate_performed_by(self):
        users = self.config.get('users', [])
        user_list = [user.split('|')[1] for user in users]  # Extract the names from the 'Name|email' format
        self.performed_by_combobox['values'] = user_list

    def select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder_path.config(text=folder)

            # set the ouptut path
            self.output_folder_path.config(text= os.path.join(folder,"out"))

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_path.config(text=folder)

    def log_message(self, message):
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)

    def run_analysis_thread(self):
        
        # Disable the "Run Analysis" button to prevent multiple clicks
        # self.run_button.config(state=tk.DISABLED)
        
        # Show progress
        self.progress_label.config(text="Running analysis...")
        self.progress_bar.start()

        # Run analysis in a separate thread
        #if self.phantom().lower() in ["catphan604", "catphan504", "qckv", "qc3"] :
        threading.Thread(target=self.run_analysis).start()
        #else:
        #    self.log_message(f"Unknown phantom type: {self.phantom()}")

    def run_analysis(self):
        
        try:
            if self.phantom().lower() in ['catphan604', 'catphan504']:
                self.run_analysis_catphan()  
            elif self.phantom().lower() == 'qckv':
                self.run_analysis_qckv()
            elif self.phantom().lower() == 'qc3':
                self.run_analysis_qc3()
            else:
                pass
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            # Re-enable the button and stop progress indicator
            self.run_button.config(state=tk.NORMAL)
            self.progress_label.config(text="Analysis completed.")
            self.progress_bar.stop()

    
    def run_analysis_qckv(self):
        import qckv

        self.phantom_config = self.load_phantom_config()

        input_dir = self.input_folder_path.cget("text")
        output_dir = self.output_folder_path.cget("text")

        if not input_dir:
            messagebox.showerror("Error", "Please select the input folder and config file.")
            return

        if not output_dir:
            output_dir = os.path.join(input_dir, 'out')

        if self.phantom().lower().strip() in ['catphan604', 'catphan504']:
            selection_mode = SelectionMode.SERIES
        else:
            selection_mode = SelectionMode.FILE
        
        dicom_chooser = DicomChooser(self.root, input_dir, selection_mode=selection_mode)
        dicom_chooser.show()

        # Use wait_window to pause execution until the selection window is closed
        self.root.wait_window(dicom_chooser.window)

        # Get the selection
        selected_file = dicom_chooser.selected_file
        self.log_message(f'selected_file={selected_file}')

        if selected_file:
            # copy all selected files 
            qckv_dir = os.path.join(output_dir, 'qckv')
            if not os.path.exists(qckv_dir):
                os.makedirs(qckv_dir)

            import shutil
            src_file = selected_file
            filename = os.path.basename(src_file)
            dst_file = os.path.join(qckv_dir, filename)
            shutil.copy(src_file, dst_file)
            
            self.analysis_input_file = dst_file
            self.analysis_result_folder = qckv_dir
        else:
            self.log_message("No files selected for analysis.")
            return


        metadata=self.phantom_config['publish_pdf_params']['metadata']
        metadata['Performed By'] = self.performed_by_combobox.get()
        metadata['Performed Date'] = self.performed_date_entry.get() 

        notes = self.notes_text.get("1.0", tk.END).strip()


        qckv.run_analysis(device_id=self.device_id(),
            input_file=self.analysis_input_file, 
            output_dir=self.analysis_result_folder, 
            config = self.phantom_config, 
            notes=notes, 
            metadata=metadata, 
            log_message=self.log_message
            )


    def run_analysis_qc3(self):
        import qc3

        self.phantom_config = self.load_phantom_config()

        input_dir = self.input_folder_path.cget("text")
        output_dir = self.output_folder_path.cget("text")

        if not input_dir:
            messagebox.showerror("Error", "Please select the input folder and config file.")
            return

        if not output_dir:
            output_dir = os.path.join(input_dir, 'out')

        if self.phantom().lower().strip() in ['catphan604', 'catphan504']:
            selection_mode = SelectionMode.SERIES
        else:
            selection_mode = SelectionMode.FILE
        
        dicom_chooser = DicomChooser(self.root, input_dir, selection_mode=selection_mode)
        dicom_chooser.show()

        # Use wait_window to pause execution until the selection window is closed
        self.root.wait_window(dicom_chooser.window)

        # Get the selection
        selected_file = dicom_chooser.selected_file
        self.log_message(f'selected_file={selected_file}')

        if selected_file:
            # copy all selected files 
            qc3_dir = os.path.join(output_dir, 'qc3')
            if not os.path.exists(qc3_dir):
                os.makedirs(qc3_dir)

            import shutil
            src_file = selected_file
            filename = os.path.basename(src_file)
            dst_file = os.path.join(qc3_dir, filename)
            shutil.copy(src_file, dst_file)
            
            self.analysis_input_file = dst_file
            self.analysis_result_folder = qc3_dir
        else:
            self.log_message("No files selected for analysis.")
            return


        metadata=self.phantom_config['publish_pdf_params']['metadata']
        metadata['Performed By'] = self.performed_by_combobox.get()
        metadata['Performed Date'] = self.performed_date_entry.get() 

        notes = self.notes_text.get("1.0", tk.END).strip()

        qc3.run_analysis(device_id=self.device_id(),
            input_file=self.analysis_input_file, 
            output_dir=self.analysis_result_folder, 
            config = self.phantom_config, 
            notes=notes, 
            metadata=metadata, 
            log_message=self.log_message
            )

    def run_analysis_catphan(self):
        import catphan

        self.phantom_config = self.load_phantom_config()

        input_dir = self.input_folder_path.cget("text")
        output_dir = self.output_folder_path.cget("text")

        if not input_dir:
            messagebox.showerror("Error", "Please select the input folder and config file.")
            return

        if not output_dir:
            output_dir = os.path.join(input_dir, 'out')

        if self.phantom().lower().strip() in ['catphan604', 'catphan504']:
            selection_mode = SelectionMode.SERIES
        else:
            selection_mode = SelectionMode.FILE
        
        dicom_chooser = DicomChooser(self.root, input_dir, selection_mode=selection_mode)
        dicom_chooser.show()

        # Use wait_window to pause execution until the selection window is closed
        self.root.wait_window(dicom_chooser.window)

        # Get the selection
        selected_series_name, selected_files = dicom_chooser.get_selection()

        if selected_files:
            self.log_message(f"Running analysis on series: {selected_series_name}")

            # copy all selected files 
            catphan_dir = os.path.join(output_dir, 'catphan')
            if not os.path.exists(catphan_dir):
                os.makedirs(catphan_dir)

            import shutil
            for src_file in selected_files:
                filename = os.path.basename(src_file)
                dst_file = os.path.join(catphan_dir, filename )
                shutil.copy(src_file, dst_file)
            
            self.analysis_input_folder = catphan_dir
            self.analysis_result_folder = catphan_dir
                
        else:
            self.log_message("No files selected for analysis.")
            return


        metadata=self.phantom_config['publish_pdf_params']['metadata']
        metadata['Performed By'] = self.performed_by_combobox.get()
        metadata['Performed Date'] = self.performed_date_entry.get() 

        notes = self.notes_text.get("1.0", tk.END).strip()


        catphan.run_analysis(device_id=self.device_id(),
            input_dir=self.analysis_input_folder, 
            output_dir=self.analysis_result_folder, 
            config = self.phantom_config, 
            notes=notes, 
            metadata=metadata, 
            log_message=self.log_message
            )



    def save_settings(self):
        # Save the current selections in a dictionary
        settings = {
            'input_folder': self.input_folder_path.cget("text"),
            'output_folder': self.output_folder_path.cget("text"),
            'performed_by': self.performed_by_combobox.get(), 
            'site': self.site_combobox.get(),
            'device': self.device_combobox.get(),
            'phantom': self.phantom_combobox.get(),
        }

        # Write the settings to the JSON file
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)

    def load_settings(self):
        # Load settings from the JSON file if it exists
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        return {}

    def on_closing(self):
        # Save the settings when the app is closed
        self.save_settings()
        self.root.destroy()

    def record_result_as_measurement1ds(self, result_data):
        # Configuration
        url = self.config['webservice_url'] + '/measurement1ds'
        app = f'{util.get_app_name()} 1.0.0'
        site_id = self.site()
        device_id = self.device()

        # travese the result object and collect numbers
        self.log_message('collecting numbers from the result file...')
        kvps = obj_helper.traverse_and_collect_numbers(result_data)

        # convert the numbers key value pairs to measurement objects
        self.log_message('converting numbers kvps to measurement1d objects...')
        measurements = model_helper.convert_kvps_to_measurement1d(key_value_pairs=kvps, 
                                                                key_prefix=f'{self.phantom().lower()}_',
                                                                device_id=f'{site_id}|{device_id}', 
                                                                app=app)

        self.log_message(f'posting the measurement1d array to the server... url={url}')
        res = webservice_helper.post_measurements(measurements, url=url)
        if res != None:
            self.log_message("post succeeded!")
            return res
        else:
            self.log_message("post failed!")
            return None

    def record_result_thread(self):
        
        if not hasattr(self, 'analysis_result_folder') or not os.path.exists(self.analysis_result_folder):
            self.log_message('Result folder not present. Please run your analysis first')

        # Disable the "Run Analysis" button to prevent multiple clicks
        self.push_to_server_button.config(state=tk.DISABLED)
        
        # Show progress
        self.progress_label.config(text="Pushing data to server...")
        self.progress_bar.start()

        # Run analysis in a separate thread
        threading.Thread(target=self.record_result).start()

    def record_result(self):

        try:
            
            if self.phantom().lower() in ['catphan604', 'catphan504']:    
                import catphan

                result_data = catphan.push_to_server(result_folder=self.analysis_result_folder, config = self.config, log_message=self.log_message)

                # post result as measurements   
                self.record_result_as_measurement1ds(result_data)
            else:
                self.log_message(f'Error: unknown phantom: {self.phantom()}')

        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            self.progress_bar.stop()

        finally:
            # Re-enable the button and stop progress indicator
            self.push_to_server_button.config(state=tk.NORMAL)
            self.progress_label.config(text="Pushing to the server completed!")
            self.progress_bar.stop()

# Main Application
if __name__ == "__main__":
    # Show the splash screen first
    show_splash_screen()

    # Start the main application after splash
    root = tk.Tk()
    app = CTQAGuiApp(root)
    root.mainloop()
