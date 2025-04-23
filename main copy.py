import sys
import os
import shutil
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
from datetime import datetime
import getpass
import socket
from tkinter.font import Font


class FileTransferLogger:
    def __init__(self, root):
        self.root = root
        self.root.title("DTA File Transfer Log")

        # Determine the base path (for PyInstaller or normal execution)
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS  # Temporary directory for PyInstaller
        else:
            base_path = os.path.dirname(__file__)  # Normal execution

        # Ensure config.ini exists in the current working directory
        config_path = os.path.join(os.getcwd(), "config.ini")
        if not os.path.exists(config_path):
            bundled_config_path = os.path.join(base_path, "config.ini")
            shutil.copy(bundled_config_path, config_path)

        # Load the config file
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

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
        date_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(left_frame, text="Username:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(left_frame, textvariable=self.username_var, width=40,
                  state="readonly").grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(left_frame, text="Computer Name:").grid(
            row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(left_frame, textvariable=self.computername_var, width=40,
                  state="readonly").grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        self._add_combobox(left_frame, "Media Type:",
                           self.media_type_var, self.media_types, 3)
        self._add_combobox(left_frame, "Media ID:", self.media_id_var, [], 4)
        self._add_combobox(left_frame, "Transfer Type:", self.transfer_type_var, list(
            self.transfer_types.keys()), 5, strict=True)
        self._add_combobox(left_frame, "Source:",
                           self.source_var, self.network_list, 6)
        self._add_combobox(left_frame, "Destination:",
                           self.destination_var, self.network_list, 7)

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
        ttk.Button(button_frame, text="Select Files/Folders",
                   command=self.select_files_and_folders).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_selected_files).grid(
            row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected_file).grid(
            row=0, column=2, sticky="ew", padx=5, pady=5)

        ttk.Label(right_frame, text="Selected Files/Folders:").grid(row=2,
                                                                    column=0, sticky="w", padx=5, pady=5)
        self.file_listbox = tk.Listbox(
            right_frame, height=10, width=60, selectmode=tk.MULTIPLE)
        self.file_listbox.grid(row=3, column=0, columnspan=2,
                               sticky="nsew", padx=5, pady=5)

        ttk.Button(right_frame, text="Generate Logs", command=self.save_logs).grid(
            row=5, column=1, sticky="e", padx=5, pady=5)

    def _add_combobox(self, frame, label, variable, options, row, strict=False):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky=tk.W)
        combobox = ttk.Combobox(
            frame, textvariable=variable, values=options, width=37)
        combobox.grid(row=row, column=1, sticky=tk.W)
        if strict:
            combobox.state(["readonly"])

    def select_files_and_folders(self):
        files = filedialog.askopenfilenames(
            title="Select Files", multiple=True)
        folder = filedialog.askdirectory(title="Select Folder (optional)")

        selected = list(files)
        if folder:
            for root, _, filenames in os.walk(folder):
                for name in filenames:
                    selected.append(os.path.join(root, name))

        # Add selected files to the listbox and internal list
        for file in selected:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.file_listbox.insert(tk.END, file)

        self.file_count_label.config(
            text=f"Files Selected: {len(self.selected_files)}")

    def remove_selected_file(self):
        # Get all selected indices
        selected_indices = self.file_listbox.curselection()
        # Remove files from the internal list and the Listbox
        # Reverse to avoid index shifting issues
        for index in reversed(selected_indices):
            file_to_remove = self.file_listbox.get(index)
            self.selected_files.remove(file_to_remove)
            self.file_listbox.delete(index)

        self.file_count_label.config(
            text=f"Files Selected: {len(self.selected_files)}")

    def clear_selected_files(self):
        # Clear the internal list and the Listbox
        self.selected_files.clear()
        self.file_listbox.delete(0, tk.END)

        # Update the file count label
        self.file_count_label.config(text="Files Selected: 0")

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

        # Get log file base names from config and append the extension if missing
        transfer_log_base_name = self.config.get(
            "LogFileNames", "TransferLog", fallback="DTATransferLog")
        file_list_base_name = self.config.get(
            "LogFileNames", "FileList", fallback="DTAFileList")

        # Automatically append .log if not already present
        if not transfer_log_base_name.endswith(".log"):
            transfer_log_base_name += ".log"
        if not file_list_base_name.endswith(".log"):
            transfer_log_base_name += ".log"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transfer_log_file = os.path.join(
            self.log_output_folder, f"transfer_log_{timestamp}.log")
        file_list_file = os.path.join(
            self.log_output_folder, f"file_list_{timestamp}.log")

        with open(transfer_log_file, "w") as f:
            f.write("Timestamp,Transfer Date,Username,Computer Name,Media Type,Media ID,Transfer Type,Source,Destination,File Count,File List\n")
            f.write(f"{datetime.now().isoformat()},"
                    f"{self.date_var.get()},"
                    f"{self.username},"
                    f"{self.computername},"
                    f"{self.media_type_var.get()},"
                    f"{self.media_id_var.get()},"
                    f"{self.transfer_type_var.get()},"
                    f"{self.source_var.get()},"
                    f"{self.destination_var.get()},"
                    f"{len(self.selected_files)},"
                    f"{transfer_log_file}\n")

        with open(file_list_file, "w") as f:
            f.write("Full Name,Size\n")
            for path in self.selected_files:
                try:
                    size = os.path.getsize(path)
                    f.write(f"{path},{size}\n")
                except Exception as e:
                    f.write(f"{path},ERROR: {str(e)}\n")

        messagebox.showinfo("Success", "Logs saved successfully.")

    def show_source_destination_warning(self):
        warning_window = tk.Toplevel(self.root)
        warning_window.title("Warning")
        warning_window.geometry("400x200")
        warning_window.grab_set()  # Make the dialog modal

        ttk.Label(
            warning_window, text="Source and Destination are the same which is highly unusual.").pack(pady=10)
        ttk.Label(warning_window, text="Please confirm to proceed.").pack(pady=5)

        confirm_var = tk.BooleanVar(value=False)
        confirm_checkbox = ttk.Checkbutton(
            warning_window, text="I understand and want to proceed", variable=confirm_var
        )
        confirm_checkbox.pack(pady=10)

        # Create the Confirm button and bind its state to the checkbox
        confirm_button = ttk.Button(
            warning_window, text="Confirm", state="disabled", command=warning_window.destroy)

        # Cancel button explicitly sets confirm_var to False
        def on_cancel():
            confirm_var.set(False)
            warning_window.destroy()

        cancel_button = ttk.Button(
            warning_window, text="Cancel", command=on_cancel)

        # Swap the positions of the Cancel and Confirm buttons
        cancel_button.pack(side=tk.LEFT, padx=20, pady=20)
        confirm_button.pack(side=tk.RIGHT, padx=20, pady=20)

        # Enable the Confirm button when the checkbox is selected
        def toggle_confirm_button(*args):
            if confirm_var.get():
                confirm_button.config(state="normal")
            else:
                confirm_button.config(state="disabled")

        confirm_var.trace_add("write", toggle_confirm_button)

        warning_window.wait_window()  # Wait for the dialog to close
        return confirm_var.get()


if __name__ == "__main__":
    root = tk.Tk()
    app = FileTransferLogger(root)
    root.mainloop()
