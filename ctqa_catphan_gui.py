import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk  # For progress bar
import threading
from util import log, obj_serializer, read_json_file
from pylinac import CatPhan604, CatPhan600, CatPhan504, CatPhan503
import time

SETTINGS_FILE = 'settings.json'

class CTQAGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CT QA using CatPhans")

        # Set the application icon (ensure app.ico is in the same directory as this script)
        self.root.iconbitmap('app.ico')

        # Load saved settings
        self.settings = self.load_settings()

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

        # Config file frame (button + label)
        self.config_frame = tk.Frame(root)
        self.config_frame.pack(pady=5, padx=5, fill="x")
        
        self.config_file_button = tk.Button(self.config_frame, text="Select Config File", command=self.select_config_file)
        self.config_file_button.pack(side="left", padx=5)
        self.config_file_path = tk.Label(self.config_frame, text=self.settings.get('config_file', ''), relief=tk.SUNKEN, anchor="w")
        self.config_file_path.pack(side="left", fill="x", expand=True)

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

    def select_input_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder_path.config(text=folder)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder_path.config(text=folder)

    def select_config_file(self):
        file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file:
            self.config_file_path.config(text=file)

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
                self.log_message(f'Unknown CatPhan model: {catphan_model}')
                return
            
            self.log_message('Running analysis...')
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
                expected_hu_values=params['expected_hu_values']
            )

            # Save the results as PDF, TXT, and JSON
            result_pdf = os.path.join(output_dir, config['publish_pdf_params']['filename'])
            self.log_message(f'Saving result PDF: {result_pdf}')
            ct.publish_pdf(result_pdf)

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
            'config_file': self.config_file_path.cget("text")
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
    root = tk.Tk()
    app = CTQAGuiApp(root)
    root.mainloop()
