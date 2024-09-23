import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry  # Date picker widget
from tkinter import ttk  # For progress bar
import threading
import time
from util import log, obj_serializer, read_json_file
from pylinac import CatPhan604, CatPhan600, CatPhan504, CatPhan503

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

class CTQAGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CTQA-CatPhans")

        # Set the application icon (ensure app.ico is in the same directory as this script)
        self.root.iconbitmap('app.ico')

        # Load saved settings
        self.settings = self.load_settings()
        

        # Config file frame (button + label)
        self.config_frame = tk.Frame(root)
        self.config_frame.pack(pady=5, padx=5, fill="x")
        
        self.config_file_button = tk.Button(self.config_frame, text="Select Config File", command=self.select_config_file)
        self.config_file_button.pack(side="left", padx=5)
        self.config_file_path = tk.Label(self.config_frame, text=self.settings.get('config_file', ''), relief=tk.SUNKEN, anchor="w")
        self.config_file_path.pack(side="left", fill="x", expand=True)

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
        
        self.output_folder_button = tk.Button(self.output_frame, text="Select Output Folder", command=self.select_output_folder)
        self.output_folder_button.pack(side="left", padx=5)
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

        # Progress bar and status label
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack(pady=5)
        self.progress_bar = ttk.Progressbar(root, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=5, pady=5)

        # Log output area
        self.log_output = tk.Text(root, height=10, wrap="word")
        self.log_output.pack(fill="x", padx=5, pady=5)

        # Set up the exit event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # after all UIs created:
        self.populate_performed_by()  # Populate the combobox with data from config file
        # Set the default value from the loaded settings, if available
        performed_by = self.settings.get('performed_by', '')
        if performed_by:
            self.performed_by_combobox.set(performed_by)

    def populate_performed_by(self):
        # Read the config file to get the 'users' array and populate the combobox
        if  self.config_file_path.cget("text"):
            config = read_json_file(self.config_file_path.cget("text"))
            users = config.get('users', [])
            user_list = [user.split('|')[1] for user in users]  # Extract the names from the 'Name|email' format
            self.performed_by_combobox['values'] = user_list
        else:
            self.performed_by_combobox['values'] = []

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

    def select_config_file(self):
        # Open the file dialog for JSON files
        file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        
        if file:
            try:
                # Try to read the file to ensure it's a valid JSON
                with open(file, 'r') as f:
                    config = json.load(f)  # Load the JSON file content
                
                # Update the label with the selected file path
                self.config_file_path.config(text=file)

                # Populate the "Performed By" dropdown (assumes 'users' in the config)
                self.populate_performed_by()
            
            except json.JSONDecodeError:
                # If the file isn't valid JSON, show an error message
                messagebox.showerror("Invalid JSON", "The selected file is not a valid JSON file. Please choose a valid JSON file.")
        
        else:
            # If no file was selected (dialog was canceled), just return
            return

    def log_message(self, message):
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)

    def run_analysis_thread(self):
        # Disable the "Run Analysis" button to prevent multiple clicks
        self.run_button.config(state=tk.DISABLED)
        
        # Show progress
        self.progress_label.config(text="Running analysis...")
        self.progress_bar.start()

        # Run analysis in a separate thread
        threading.Thread(target=self.run_analysis).start()

    def run_analysis(self):
        try:
            input_dir = self.input_folder_path.cget("text")
            output_dir = self.output_folder_path.cget("text")
            config_file = self.config_file_path.cget("text")

            if not input_dir or not config_file:
                messagebox.showerror("Error", "Please select the input folder and config file.")
                return

            if not output_dir:
                output_dir = os.path.join(input_dir, 'out')

            self.log_message(f'Input directory: {input_dir}')
            self.log_message(f'Output directory: {output_dir}')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            self.log_message(f'Config file: {config_file}')
            config = read_json_file(config_file)

            # Catphan analysis logic
            catphan_model = config['catphan_model']
            self.log_message(f'Phantom model: {catphan_model}')
            
            if catphan_model == '604':
                ct = CatPhan604(input_dir)
            elif catphan_model == '600':
                ct = CatPhan600(input_dir)
            elif catphan_model == '504':
                ct = CatPhan504(input_dir)
            elif catphan_model == '503':
                ct = CatPhan503(input_dir)
            else:
                self.log_message(f'Error:Unknown CatPhan model: {catphan_model}!')
                return
            
            self.log_message('Running analysis...')
            params = config['analysis_params']
            ct.analyze(
                hu_tolerance=params['hu_tolerance'],
                scaling_tolerance=params['scaling_tolerance'],
                thickness_tolerance=params['thickness_tolerance'],
                low_contrast_tolerance=params['low_contrast_tolerance'],
                cnr_threshold=params['cnr_threshold'],
                #zip_after=params['zip_after'],
                zip_after=False,
                contrast_method=params['contrast_method'],
                visibility_threshold=params['visibility_threshold'],
                thickness_slice_straddle=params['thickness_slice_straddle'],
                expected_hu_values=params['expected_hu_values']
            )

            # Save the results as PDF, TXT, and JSON
            result_pdf = os.path.join(output_dir, config['publish_pdf_params']['filename'])
            self.log_message(f'Saving result PDF: {result_pdf}')
            params = config['publish_pdf_params']

            metadata=params['metadata']
            metadata['Performed By'] = self.performed_by_combobox.get()
            metadata['Performed Date'] = self.performed_date_entry.get() 
            
            notes = self.notes_text.get("1.0", tk.END).strip()


            ct.publish_pdf(
                filename=result_pdf,
                notes=notes,
                open_file=True,
                metadata=metadata,    
                logo=params['logo']
            )

            result_txt = os.path.join(output_dir, 'result.txt')
            self.log_message(f'Saving result TXT: {result_txt}')
            with open(result_txt, 'w') as file:
                file.write(ct.results())

            result = ct.results_data()
            result_json = os.path.join(output_dir, 'result.json')
            result_dict = json.loads(json.dumps(vars(result), default=obj_serializer))
            self.log_message(f'Saving result JSON: {result_json}')
            with open(result_json, 'w') as json_file:
                json.dump(result_dict, json_file, indent=4)

            self.log_message('Analysis completed.')

        except Exception as e:
            self.log_message(f"Error: {str(e)}")

        finally:
            # Re-enable the button and stop progress indicator
            self.run_button.config(state=tk.NORMAL)
            self.progress_label.config(text="Analysis completed.")
            self.progress_bar.stop()

    def save_settings(self):
        # Save the current selections in a dictionary
        settings = {
            'input_folder': self.input_folder_path.cget("text"),
            'output_folder': self.output_folder_path.cget("text"),
            'config_file': self.config_file_path.cget("text"),
            'performed_by': self.performed_by_combobox.get()  # Save the selected value from the combobox
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

# Main Application
if __name__ == "__main__":
    # Show the splash screen first
    show_splash_screen()

    # Start the main application after splash
    root = tk.Tk()
    app = CTQAGuiApp(root)
    root.mainloop()
