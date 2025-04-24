import configparser
import getpass
import gzip
import hashlib
import io
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tkinter as tk
import zipfile
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from tkinter.font import Font
from tkcalendar import DateEntry
from ttkthemes import ThemedTk


class FileTransferLogger:
    def __init__(self, root):
        self.root = root
        self.root.title("DTA File Transfer Log")

        # Determine the base path (for PyInstaller or normal execution)
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        # Ensure config.ini exists in the current working directory
        config_path = os.path.join(os.getcwd(), "config.ini")
        if not os.path.exists(config_path):
            bundled_config_path = os.path.join(base_path, "config.ini")
            shutil.copy(bundled_config_path, config_path)

        # Load the config file
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        # Apply theme if using ThemedTk
        if isinstance(self.root, ThemedTk):
            theme = self.config.get("UI", "Theme", fallback="arc")
            try:
                self.root.set_theme(theme)
            except:
                # Fallback to default theme if the specified theme is not available
                self.root.set_theme("arc")

        # Update the icon path to use the resources folder
        icon_path = os.path.join(os.path.dirname(
            __file__), "resources", "dtatransferlog.png")
        icon = tk.PhotoImage(file=icon_path)
        self.root.iconphoto(True, icon)

        self.selected_files = []

        # Initialize variables
        self.date_var = tk.StringVar()
        self.media_type_var = tk.StringVar()
        self.media_id_var = tk.StringVar()
        self.transfer_type_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self.destination_var = tk.StringVar()
        self.log_output_var = tk.StringVar(value="")
        self.open_transfer_log_var = tk.BooleanVar(value=False)
        self.open_file_list_log_var = tk.BooleanVar(value=False)
        self.include_sha256_var = tk.BooleanVar(value=False)
        self.username = getpass.getuser()
        self.computername = socket.gethostname()

        # Create StringVars for username and computername
        self.username_var = tk.StringVar(value=self.username)
        self.computername_var = tk.StringVar(value=self.computername)

        # Convert log output folder to an absolute path
        self.log_output_folder = os.path.abspath(
            self.config.get("Paths", "LogOutputFolder", fallback="./logs")
        )
        # Update the GUI variable
        self.log_output_var.set(self.log_output_folder)

        self.media_types = self._get_config_list("MediaTypes", "Options")
        self.transfer_types = self._get_transfer_types()
        self.network_list = self._get_config_list("NetworkList", "Options")

        self._build_ui()

    def _get_config_list(self, section, option):
        items = self.config.get(section, option, fallback="")
        return [item.strip() for item in items.split(",") if item.strip()]

    def _get_transfer_types(self):
        items = self.config.get("TransferTypes", "Options", fallback="")
        mapping = {}
        for pair in items.split(","):
            if ":" in pair:
                name, abbr = pair.split(":", 1)
                mapping[name.strip()] = abbr.strip()
        return mapping

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        # Configure the root window to expand
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Configure the frame to expand
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=0)  # Left column fixed size
        frame.grid_columnconfigure(1, weight=1)  # Right column resizable

        # Left Column
        left_frame = ttk.Frame(frame, padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Right Column
        right_frame = ttk.Frame(frame, padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Configure the right frame to expand
        # Allow the listbox row to expand
        right_frame.grid_rowconfigure(3, weight=1)
        right_frame.grid_rowconfigure(4, weight=0)  # Spacer row (if needed)
        # Generate Logs button row does not expand
        right_frame.grid_rowconfigure(5, weight=0)
        right_frame.grid_columnconfigure(
            0, weight=0)  # Label column fixed size
        right_frame.grid_columnconfigure(1, weight=1)  # Entry column resizable

        # Left Column Widgets
        ttk.Label(left_frame, text="Transfer Date:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        date_entry = DateEntry(
            left_frame, textvariable=self.date_var, width=37, date_pattern="mm/dd/yyyy", maxdate=datetime.now()
        )
        date_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(left_frame, text="Username:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(left_frame, textvariable=self.username_var, width=39,
                  state="readonly").grid(row=1, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(left_frame, text="Computer Name:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(left_frame, textvariable=self.computername_var, width=39,
                  state="readonly").grid(row=2, column=1, sticky="w", padx=5, pady=5)

        self._add_combobox(left_frame, "Media Type:",
                           self.media_type_var, self.media_types, 3)
        self._add_combobox(left_frame, "Media ID:", self.media_id_var, [], 4)
        self._add_combobox(left_frame, "Transfer Type:", self.transfer_type_var, list(
            self.transfer_types.keys()), 5, strict=True)
        self._add_combobox(left_frame, "Source:",
                           self.source_var, self.network_list, 6)
        self._add_combobox(left_frame, "Destination:",
                           self.destination_var, self.network_list, 7)

        checkbox_frame = ttk.Frame(left_frame)
        checkbox_frame.grid(row=8, column=0, columnspan=2,
                            sticky="e", padx=5, pady=5)

        ttk.Checkbutton(
            checkbox_frame,
            text="Open Transfer Log",
            variable=self.open_transfer_log_var
        ).grid(row=0, column=0, sticky="w", padx=5)

        ttk.Checkbutton(
            checkbox_frame,
            text="Open File List Log",
            variable=self.open_file_list_log_var
        ).grid(row=0, column=1, sticky="w", padx=5)

        # Add SHA-256 option checkbox
        ttk.Checkbutton(
            checkbox_frame,
            text="Include SHA-256 Checksums",
            variable=self.include_sha256_var
        ).grid(row=0, column=2, sticky="w", padx=5)

        # Right Column Widgets
        ttk.Label(right_frame, text="Log Output Folder:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)

        # Dynamically set the width of the entry based on the text length
        font = Font(font="TkDefaultFont")
        text_width = font.measure(
            self.log_output_var.get()) // font.measure("0") + 2  # Add padding
        ttk.Entry(right_frame, width=text_width, state="readonly", textvariable=self.log_output_var).grid(
            row=0, column=1, sticky="w", padx=5, pady=5)

        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=1, column=0, columnspan=2,
                          sticky="ew", padx=5, pady=5)

        ttk.Button(button_frame, text="Select Files",
                   command=self.select_files).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(button_frame, text="Select Folders",
                   command=self.select_folders).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_selected_files).grid(
            row=0, column=2, sticky="ew", padx=5, pady=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected_file).grid(
            row=0, column=3, sticky="ew", padx=5, pady=5)

        ttk.Label(right_frame, text="Selected Files:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)

        # Add a frame to hold the listbox and scrollbar
        listbox_frame = ttk.Frame(right_frame)
        listbox_frame.grid(row=3, column=0, columnspan=2,
                           sticky="nsew", padx=5, pady=5)

        # Configure the frame to expand
        listbox_frame.grid_rowconfigure(0, weight=1)
        listbox_frame.grid_columnconfigure(0, weight=1)

        # Add the listbox
        self.file_listbox = tk.Listbox(
            listbox_frame, height=10, width=60, selectmode=tk.MULTIPLE)
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(
            listbox_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.config(yscrollcommand=scrollbar.set)

        # Add file count label and Generate Logs button
        file_count_frame = ttk.Frame(right_frame)
        file_count_frame.grid(row=5, column=0, columnspan=2,
                              sticky="ew", padx=5, pady=5)

        # Configure column weights to allow the label to expand
        file_count_frame.columnconfigure(0, weight=1)
        file_count_frame.columnconfigure(1, weight=0)

        # File count label
        self.file_count_label = ttk.Label(
            file_count_frame, text="Files Selected: 0")
        self.file_count_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Generate Logs button
        ttk.Button(file_count_frame, text="Generate Logs", command=self.save_logs).grid(
            row=0, column=1, sticky="e", padx=5, pady=5
        )

        # Add status bar at the bottom
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.grid(row=1, column=0, sticky="ew")
        self.root.grid_rowconfigure(1, weight=0)

    def _add_combobox(self, frame, label, variable, options, row, strict=False):
        ttk.Label(frame, text=label).grid(
            row=row, column=0, sticky="w", padx=5, pady=5)
        combobox = ttk.Combobox(
            frame, textvariable=variable, values=options, width=37)
        combobox.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        if strict:
            combobox.state(["readonly"])

    def _update_listbox(self):
        self.selected_files = sorted(self.selected_files)
        self.file_listbox.delete(0, tk.END)  # Clear the listbox
        for file in self.selected_files:
            self.file_listbox.insert(tk.END, file)
        # Update the file count label
        self.file_count_label.config(
            text=f"Files Selected: {len(self.selected_files)}")

    def select_files(self):
        self.status_var.set("Selecting files...")
        files = filedialog.askopenfilenames(
            title="Select Files", multiple=True
        )
        # Add selected files to the listbox and internal list
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)

        self._update_listbox()
        self.status_var.set(f"Added {len(files)} files")

    def select_folders(self):
        self.status_var.set("Selecting folder...")
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self.status_var.set(f"Processing folder: {folder}")
            self.root.update()  # Update the UI to show the status message

            file_count = 0
            for root, _, filenames in os.walk(folder):
                for name in filenames:
                    file_path = os.path.join(root, name)
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        file_count += 1

                    # Update status periodically for large folders
                    if file_count % 100 == 0:
                        self.status_var.set(
                            f"Added {file_count} files from {folder}")
                        self.root.update_idletasks()  # Update UI without blocking

            self._update_listbox()
            self.status_var.set(f"Added {file_count} files from folder")
        else:
            self.status_var.set("Folder selection cancelled")

    def remove_selected_file(self):
        selected_indices = self.file_listbox.curselection()
        # Remove files from the internal list and the Listbox
        for index in reversed(selected_indices):
            file_to_remove = self.file_listbox.get(index)
            self.selected_files.remove(file_to_remove)
            self.file_listbox.delete(index)

        self._update_listbox()

    def clear_selected_files(self):
        # Clear the internal list and the Listbox
        self.selected_files.clear()
        self._update_listbox()

    def save_logs(self):
        # Check if mandatory fields are filled
        if not self.media_type_var.get():
            messagebox.showwarning("Warning", "Media Type is required.")
            return
        if not self.media_id_var.get():
            messagebox.showwarning("Warning", "Media ID is required.")
            return
        if not self.transfer_type_var.get():
            messagebox.showwarning("Warning", "Transfer Type is required.")
            return
        if not self.source_var.get():
            messagebox.showwarning("Warning", "Source is required.")
            return
        if not self.destination_var.get():
            messagebox.showwarning("Warning", "Destination is required.")
            return

        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected.")
            return

        # Check if source and destination are the same
        if self.source_var.get() == self.destination_var.get():
            proceed = self.show_source_destination_warning()
            if not proceed:
                return

        # Ensure the log output folder exists when generating logs
        os.makedirs(self.log_output_folder, exist_ok=True)

        # Generate the file_list_log_name
        current_date = datetime.now().strftime("%Y%m%d")
        username = self.username
        transfer_type_abbr = self.transfer_types.get(
            self.transfer_type_var.get(), "UNK")
        source = self.source_var.get()
        destination = self.destination_var.get()
        base_name = f"{current_date}_{username}_{transfer_type_abbr}_{source}-{destination}"

        # Increment the counter for unique file names
        counter = 1
        while True:
            file_list_log_name = f"{base_name}_{counter:03d}.log"
            file_list_log_path = os.path.join(
                self.log_output_folder, file_list_log_name)
            if not os.path.exists(file_list_log_path):
                break
            counter += 1

        include_sha256 = self.include_sha256_var.get()

        # Write the selected files and their sizes to the file list log
        total_file_count = 0
        with open(file_list_log_path, "w") as file_list_log:
            # Write header
            if include_sha256:
                file_list_log.write(
                    '"Level","Container","FullName","Size","SHA256"\n')
            else:
                file_list_log.write('"Level","Container","FullName","Size"\n')

            def sha256sum(filename):
                """Compute SHA-256 hash of a file."""
                h = hashlib.sha256()
                try:
                    with open(filename, "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            h.update(chunk)
                    return h.hexdigest()
                except Exception:
                    return "ERROR"

            def write_file_entry(level, container, full_name, size):
                """Helper function to write a file entry to the log."""
                if include_sha256:
                    if os.path.isfile(full_name):
                        sha256 = sha256sum(full_name)
                    else:
                        sha256 = ""  # No SHA256 for files inside archives or non-files
                    file_list_log.write(
                        f'"{level}","{container}","{full_name}","{size}","{sha256}"\n')
                else:
                    file_list_log.write(
                        f'"{level}","{container}","{full_name}","{size}"\n')

            def process_zip_file(zip_path_or_file, level, container_name=None):
                """Process a ZIP file and write its contents to the log."""
                try:
                    # Open the ZIP file (can be a file path or a file-like object)
                    with zipfile.ZipFile(zip_path_or_file, 'r') as zip_ref:
                        for file_info in zip_ref.infolist():
                            # Only log files, not directories
                            if not file_info.is_dir():
                                # Use the provided container name or fallback to the current ZIP file name
                                current_container = container_name or os.path.basename(
                                    zip_ref.filename or "In-Memory ZIP")
                                write_file_entry(
                                    level + 1, current_container, file_info.filename, file_info.file_size)

                                # Check if the file inside the ZIP is another ZIP file
                                if file_info.filename.endswith(".zip"):
                                    # Extract the nested ZIP file to memory
                                    with zip_ref.open(file_info.filename) as nested_zip_file:
                                        # Use BytesIO to handle the nested ZIP file in memory
                                        nested_zip_data = io.BytesIO(
                                            nested_zip_file.read())
                                        # Recursively process the nested ZIP file
                                        process_zip_file(
                                            nested_zip_data, level + 1, file_info.filename)
                except zipfile.BadZipFile:
                    messagebox.showerror(
                        "Error", f"Invalid ZIP file: {zip_path_or_file}")
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"An error occurred while processing ZIP file: {zip_path_or_file}\n{e}")

            def process_tar_file(tar_path_or_file, level, container_name=None):
                """Process a TAR file and write its contents to the log."""
                try:
                    # Open the TAR file (can be a file path or a file-like object)
                    if isinstance(tar_path_or_file, str):
                        tar_ref = tarfile.open(tar_path_or_file, mode="r:*")
                    else:
                        tar_ref = tarfile.open(
                            fileobj=tar_path_or_file, mode="r:*")

                    with tar_ref:
                        for member in tar_ref.getmembers():
                            # Only log files, not directories
                            if member.isfile():
                                # Use the provided container name or fallback to the current TAR file name
                                current_container = container_name or os.path.basename(
                                    tar_ref.name or "In-Memory TAR"
                                )
                                write_file_entry(
                                    level + 1, current_container, member.name, member.size
                                )

                                # Check if the file inside the TAR is another TAR file
                                if member.name.endswith(".tar"):
                                    # Extract the nested TAR file to memory
                                    nested_tar_data = tar_ref.extractfile(
                                        member)
                                    if nested_tar_data:
                                        # Recursively process the nested TAR file
                                        process_tar_file(
                                            io.BytesIO(
                                                nested_tar_data.read()), level + 1, member.name
                                        )
                except tarfile.TarError:
                    messagebox.showerror(
                        "Error", f"Invalid TAR file: {tar_path_or_file}"
                    )
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"An error occurred while processing TAR file: {tar_path_or_file}\n{e}"
                    )

            def process_gz_file(gz_path_or_file, level, container_name=None):
                """Process a GZ file and write its contents to the log."""
                try:
                    # Open the GZ file (can be a file path or a file-like object)
                    with gzip.open(gz_path_or_file, mode="rb") as gz_ref:
                        # Use the provided container name or fallback to the current GZ file name
                        current_container = container_name or os.path.basename(
                            gz_path_or_file if isinstance(gz_path_or_file, str) else "In-Memory GZ")

                        # Read the content
                        content = gz_ref.read()
                        extracted_file_size = len(content)

                        extracted_file_name = current_container.replace(
                            ".gz", "")
                        write_file_entry(
                            level + 1, current_container, extracted_file_name, extracted_file_size)

                        # If the extracted file is a tar file, process it recursively
                        if extracted_file_name.endswith(".tar"):
                            # Use BytesIO to handle the extracted tar file in memory
                            extracted_tar_data = io.BytesIO(content)
                            process_tar_file(
                                extracted_tar_data, level + 1, extracted_file_name)
                except gzip.BadGzipFile:
                    messagebox.showerror(
                        "Error", f"Invalid GZ file: {gz_path_or_file}")
                except Exception as e:
                    messagebox.showerror(
                        "Error", f"An error occurred while processing GZ file: {gz_path_or_file}\n{e}")

            # --- Progress Bar for File Processing ---
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Generating Logs")
            progress_window.geometry("350x100")
            ttk.Label(progress_window, text="Processing files...").pack(pady=10)
            progress = ttk.Progressbar(
                progress_window, mode="determinate", length=300)
            progress.pack(pady=10)
            progress["maximum"] = len(self.selected_files)
            progress["value"] = 0
            self.root.update_idletasks()
            # --- End Progress Bar Setup ---

            # Process each selected file
            for idx, file in enumerate(self.selected_files):
                if os.path.isfile(file):
                    file_size = os.path.getsize(file)
                    write_file_entry(0, "", file, file_size)
                    total_file_count += 1

                    if file.endswith(".zip"):
                        process_zip_file(file, 0)
                    elif file.endswith(".tar"):
                        process_tar_file(file, 0)
                    elif file.endswith(".gz"):
                        process_gz_file(file, 0)

                # --- Update Progress Bar ---
                progress["value"] = idx + 1
                progress_window.update()
                # --- End Progress Update ---

            progress_window.destroy()

        # Generate the transfer log file name
        current_year = datetime.now().strftime("%Y")
        transfer_log_name = f"TransferLog_{current_year}.log"
        transfer_log_path = os.path.join(
            self.log_output_folder, transfer_log_name)

        # Append transfer details to the transfer log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        transfer_date = datetime.strptime(
            self.date_var.get(), "%m/%d/%Y").strftime("%Y-%m-%d")
        transfer_log_entry = (
            f'"{timestamp}","{transfer_date}","{username}","{self.computername}",'
            f'"{self.media_type_var.get()}","{self.media_id_var.get()}",'
            f'"{self.transfer_type_var.get()}","{source}","{destination}",'
            f'"{total_file_count}","{file_list_log_path}"\n'
        )

        # Check if the transfer log file exists
        file_exists = os.path.exists(transfer_log_path)
        with open(transfer_log_path, "a") as transfer_log:
            # Write the header if the file is being created
            if not file_exists:
                transfer_log.write(
                    '"Timestamp","Transfer Date","Username","ComputerName","MediaType","MediaID",'
                    '"TransferType","Source","Destination","File Count","File Log"\n'
                )
            # Write the transfer log entry
            transfer_log.write(transfer_log_entry)

        # Notify the user
        messagebox.showinfo("Success", f"File list log saved successfully as {file_list_log_name}.\n"
                            f"Transfer log updated: {transfer_log_name}.")
        self.status_var.set("Logs generated successfully")

        # Open the log files if the checkboxes are checked
        if self.open_transfer_log_var.get():
            self.open_file(transfer_log_path)

        if self.open_file_list_log_var.get():
            self.open_file(file_list_log_path)

    def open_file(self, file_path):
        """Open a file with the default system application."""
        try:
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform.startswith('darwin'):  # macOS
                subprocess.call(('open', file_path))
            else:  # Linux and other Unix-like
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def show_source_destination_warning(self):
        warning_window = tk.Toplevel(self.root)
        warning_window.title("Warning")
        warning_window.geometry("400x200")
        warning_window.grab_set()

        ttk.Label(
            warning_window, text="Source and Destination are the same which is highly unusual.").pack(pady=10)
        ttk.Label(warning_window, text="Please confirm to proceed.").pack(pady=5)

        confirm_var = tk.BooleanVar(value=False)
        confirm_checkbox = ttk.Checkbutton(
            warning_window, text="I understand and want to proceed", variable=confirm_var
        )
        confirm_checkbox.pack(pady=10)

        confirm_button = ttk.Button(
            warning_window, text="Confirm", state="disabled", command=warning_window.destroy)

        # Cancel button explicitly sets confirm_var to False
        def on_cancel():
            confirm_var.set(False)
            warning_window.destroy()

        cancel_button = ttk.Button(
            warning_window, text="Cancel", command=on_cancel)

        cancel_button.pack(side=tk.LEFT, padx=20, pady=20)
        confirm_button.pack(side=tk.RIGHT, padx=20, pady=20)

        # Enable the Confirm button when the checkbox is selected
        def toggle_confirm_button(*args):
            if confirm_var.get():
                confirm_button.config(state="normal")
            else:
                confirm_button.config(state="disabled")

        confirm_var.trace_add("write", toggle_confirm_button)

        warning_window.wait_window()
        return confirm_var.get()

    def process_large_collection(self, files):
        """Process a large collection of files with progress updates."""
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Processing Files")
        progress_window.geometry("300x100")

        ttk.Label(progress_window, text="Processing files...").pack(pady=10)
        progress = ttk.Progressbar(
            progress_window, mode="determinate", length=250)
        progress.pack(pady=10)

        total_files = len(files)
        progress["maximum"] = total_files

        for i, file in enumerate(files):
            self.process_file(file)
            progress["value"] = i + 1
            progress_window.update()

        progress_window.destroy()


if __name__ == "__main__":
    root = ThemedTk(theme="arc")  # Use ThemedTk instead of tk.Tk
    app = FileTransferLogger(root)
    root.mainloop()
