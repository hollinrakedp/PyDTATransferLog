import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime


class TransferLogReviewer:
    def __init__(self, root):
        self.root = root
        self.root.title("DTA Transfer Log Reviewer")

        # Set the application icon
        icon_path = os.path.join(os.path.dirname(
            __file__), "resources", "dtatransferlog.png")
        if os.path.exists(icon_path):
            icon = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, icon)

        # Frame for year selection
        year_frame = ttk.Frame(self.root, padding=10)
        year_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(year_frame, text="Select Year:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5)
        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        self.year_combobox = ttk.Combobox(
            year_frame, textvariable=self.year_var, state="readonly", width=10)
        self.year_combobox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.year_combobox.bind("<<ComboboxSelected>>", self.load_log_file)

        # Create a PanedWindow to hold the upper and lower frames
        paned_window = ttk.PanedWindow(self.root, orient="vertical")
        paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Frame for log content display (upper pane)
        log_frame = ttk.Frame(paned_window, padding=10)
        # Set initial weight for the upper pane
        paned_window.add(log_frame, weight=3)

        # Frame for transfer details (lower pane)
        details_frame = ttk.Frame(paned_window, padding=10)
        # Set initial weight for the lower pane
        paned_window.add(details_frame, weight=7)

        # Configure the root window to expand
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Add a Treeview widget to display the log content
        self.log_tree = ttk.Treeview(log_frame, columns=(
            "Timestamp", "Transfer Date", "Username", "ComputerName", "MediaType",
            "MediaID", "TransferType", "Source", "Destination", "File Count", "File Log"
        ), show="headings", height=15)
        self.log_tree.grid(row=0, column=0, sticky="nsew")

        # Configure Treeview columns
        for col in self.log_tree["columns"]:
            self.log_tree.heading(col, text=col, anchor="w")
            self.log_tree.column(col, anchor="w", width=100)

        # Add scrollbars for the log_tree
        y_scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_tree.yview)
        y_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_tree.config(yscrollcommand=y_scrollbar.set)

        x_scrollbar = ttk.Scrollbar(
            log_frame, orient="horizontal", command=self.log_tree.xview)
        x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.log_tree.config(xscrollcommand=x_scrollbar.set)

        # Configure the log frame to expand
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # Add a Treeview widget for file transfer details
        self.details_tree = ttk.Treeview(details_frame, columns=(
            "Level", "Container", "Full Name", "Size"), show="headings", height=10)
        self.details_tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Configure Treeview columns
        column_widths = {
            "Level": 35,
            "Container": 200,
            "Full Name": 500,
            "Size": 60
        }

        for col in self.details_tree["columns"]:
            self.details_tree.heading(col, text=col, anchor="w", command=lambda _col=col: self.sort_treeview(
                self.details_tree, _col, False))
            if col == "Level":
                # Prevent auto-expansion
                self.details_tree.column(
                    col, anchor="w", width=column_widths[col], stretch=False)
            elif col == "Size":
                # Anchor to the right and prevent resizing
                self.details_tree.column(
                    col, anchor="e", width=column_widths[col], stretch=False)
            else:
                self.details_tree.column(
                    col, anchor="w", width=column_widths[col])

        # Add scrollbars for the details_tree
        details_y_scrollbar = ttk.Scrollbar(
            details_frame, orient="vertical", command=self.details_tree.yview)
        details_y_scrollbar.grid(row=1, column=1, sticky="ns")
        self.details_tree.config(yscrollcommand=details_y_scrollbar.set)

        details_x_scrollbar = ttk.Scrollbar(
            details_frame, orient="horizontal", command=self.details_tree.xview)
        details_x_scrollbar.grid(row=2, column=0, sticky="ew")
        self.details_tree.config(xscrollcommand=details_x_scrollbar.set)

        # Configure the details frame to expand
        details_frame.grid_rowconfigure(1, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)

        # Bind selection event
        self.log_tree.bind("<<TreeviewSelect>>", self.display_transfer_details)

        # Load available years and the current year's log file
        self.load_available_years()
        self.load_log_file()

    def load_available_years(self):
        """Load available years based on log files in the logs directory."""
        logs_dir = os.path.abspath("./logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        years = set()
        for file_name in os.listdir(logs_dir):
            if file_name.startswith("TransferLog_") and file_name.endswith(".log"):
                year = file_name.split("_")[1].split(".")[0]
                years.add(year)

        self.year_combobox["values"] = sorted(years)

    def load_log_file(self, event=None):
        """Load the log file for the selected year."""
        selected_year = self.year_var.get()
        log_file_path = os.path.abspath(
            f"./logs/TransferLog_{selected_year}.log")

        if not os.path.exists(log_file_path):
            messagebox.showwarning(
                "Warning", f"No log file found for the year {selected_year}.")
            self.log_tree.delete(*self.log_tree.get_children())
            return

        self.display_log_content(log_file_path)

    def display_log_content(self, log_file_path):
        """Display the content of the selected log file in the Treeview."""
        try:
            # Clear existing content
            self.log_tree.delete(*self.log_tree.get_children())

            with open(log_file_path, "r") as log_file:
                lines = log_file.readlines()

            # Skip the header row
            for line in lines[1:]:
                values = line.strip().strip('"').split('","')
                self.log_tree.insert("", "end", values=values)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read log file:\n{e}")

    def display_transfer_details(self, event):
        """Display details of the selected transfer."""
        selected_item = self.log_tree.selection()
        if not selected_item:
            return

        values = self.log_tree.item(selected_item[0], "values")
        file_log_path = values[10]  # File Log column

        if not os.path.exists(file_log_path):
            messagebox.showerror(
                "Error", f"File log not found: {file_log_path}")
            return

        try:
            # Clear existing content
            self.details_tree.delete(*self.details_tree.get_children())

            with open(file_log_path, "r") as file_log:
                lines = file_log.readlines()

            # Skip the header row
            # Use `index` to ensure unique IDs
            for index, line in enumerate(lines[1:]):
                values = line.strip().strip('"').split('","')
                if len(values) == 4:  # Ensure the row has the expected number of columns
                    # Convert the "Size" column to human-readable format
                    values[3] = format_size(values[3])
                self.details_tree.insert(
                    "", "end", iid=f"{index}", values=values)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file log:\n{e}")

    def sort_treeview(self, treeview, col, reverse):
        """Sort the Treeview by a given column."""
        data = [(treeview.set(child, col), child)
                for child in treeview.get_children("")]
        data.sort(reverse=reverse)

        for index, (val, child) in enumerate(data):
            treeview.move(child, "", index)

        treeview.heading(col, command=lambda: self.sort_treeview(
            treeview, col, not reverse))


def format_size(size_in_bytes):
    """Convert file size to a human-readable format."""
    try:
        size_in_bytes = int(size_in_bytes)
        if size_in_bytes < 1024:
            return f"{size_in_bytes} B"
        elif size_in_bytes < 1024 ** 2:
            return f"{size_in_bytes / 1024:.2f} KB"
        elif size_in_bytes < 1024 ** 3:
            return f"{size_in_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_in_bytes / (1024 ** 3):.2f} GB"
    except ValueError:
        return size_in_bytes  # Return the original value if conversion fails


if __name__ == "__main__":
    root = tk.Tk()
    app = TransferLogReviewer(root)
    root.mainloop()
