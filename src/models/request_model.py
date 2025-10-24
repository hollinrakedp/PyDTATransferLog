import os
import csv
import datetime
from dataclasses import dataclass
from typing import List, Optional, Dict
from constants import REQUEST_LOG_HEADERS, REQUEST_FILE_LIST_HEADERS
from utils.file_utils import format_filename


@dataclass
class RequestFileInfo:
    """Class for tracking file information in requests"""
    path: str
    sha256: str = ""
    size: Optional[int] = None

    @property
    def name(self) -> str:
        """Get the file name"""
        return os.path.basename(self.path)

    @property
    def directory(self) -> str:
        """Get the directory containing the file"""
        return os.path.dirname(self.path)

    @property
    def size_str(self) -> str:
        """Get the file size as a string"""
        if self.size is None:
            try:
                self.size = os.path.getsize(self.path)
            except:
                return ""

        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024*1024:
            return f"{self.size/1024:.2f} KB"
        elif self.size < 1024*1024*1024:
            return f"{self.size/(1024*1024):.2f} MB"
        else:
            return f"{self.size/(1024*1024*1024):.2f} GB"


class RequestLog:
    """Class representing a file transfer request"""

    def __init__(self, config, timestamp, request_date, requestor, computer_name,
                 purpose, file_count=0, total_size=0):
        self.config = config
        self.request_dir = self.config.get("Requests", "OutputFolder", fallback="./requests")
        self.timestamp = timestamp
        self.request_date = request_date
        self.requestor = requestor
        self.computer_name = computer_name
        self.purpose = purpose
        self.file_count = file_count
        self.total_size = total_size
        self.files: List[RequestFileInfo] = []

    def add_file(self, file_info: RequestFileInfo):
        """Add a file to the request"""
        self.files.append(file_info)
        # Update file count
        self.file_count = len(self.files)

    def _save_file_list_with_progress(self, file_list_dir, selected_files, file_hashes, progress_callback, is_canceled_callback):
        """Save the file list CSV with progress reporting"""
        # Generate filename using config tokens
        file_list_name_template = self.config.get("Requests", "FileListName", fallback="{date:yyyyMMdd}_{username}_Request_{counter}.csv")
        
        # Get current date and time for token replacement
        now = datetime.datetime.now()
        date_format = self.config.get("Requests", "DateFormat", fallback="yyyyMMdd")
        time_format = self.config.get("Requests", "TimeFormat", fallback="HHmmss")
        
        # Replace tokens
        file_list_name = file_list_name_template.replace("{date:yyyyMMdd}", now.strftime("%Y%m%d"))
        file_list_name = file_list_name.replace("{date}", now.strftime(date_format.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")))
        file_list_name = file_list_name.replace("{time}", now.strftime(time_format.replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")))
        file_list_name = file_list_name.replace("{timestamp}", now.strftime("%Y%m%d-%H%M%S"))
        file_list_name = file_list_name.replace("{username}", self.requestor)
        file_list_name = file_list_name.replace("{computername}", self.computer_name)
        file_list_name = file_list_name.replace("{year}", now.strftime("%Y"))
        
        # Handle counter - find next available number
        counter = 1
        while True:
            test_name = file_list_name.replace("{counter}", f"{counter:03d}")
            test_path = os.path.join(file_list_dir, test_name)
            if not os.path.exists(test_path):
                file_list_name = test_name
                break
            counter += 1
            if counter > 999:  # Prevent infinite loop
                file_list_name = file_list_name.replace("{counter}", "999")
                break

        file_list_path = os.path.join(file_list_dir, file_list_name)
        
        # Create the CSV file
        with open(file_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            
            # Write headers
            writer.writerow(REQUEST_FILE_LIST_HEADERS)
            
            # Process files with progress reporting
            total_files = len(selected_files)
            for i, file_path in enumerate(selected_files):
                # Check if operation was canceled
                if is_canceled_callback():
                    return ""
                
                try:
                    # Get file info
                    file_size = os.path.getsize(file_path)
                    file_hash = file_hashes.get(file_path, "")
                    
                    # Write row (Level 0 for all files in request - no archive processing for requests)
                    writer.writerow([
                        "0",                    # Level
                        "",                     # Container (empty for top-level files)
                        file_path,              # FullName (complete path)
                        str(file_size),         # Size
                        file_hash               # File Hash
                    ])
                    
                except Exception as e:
                    # Write error row
                    writer.writerow([
                        "0",
                        "",
                        file_path,
                        "ERROR",
                        f"ERROR: {str(e)}"
                    ])
                
                # Update progress
                try:
                    progress = int((i + 1) / total_files * 100)
                    if progress_callback:
                        progress_callback.emit(progress)
                except Exception as e:
                    # If progress update fails, just continue (don't write error row)
                    print(f"Progress update failed: {str(e)}")
        
        return file_list_path

    def _save_request_log(self, csv_file, formatted_timestamp, file_list_path):
        """Save the request summary to the annual request log"""
        # Write the log entry to the CSV file
        file_exists = os.path.isfile(csv_file)
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            # Write headers if file is new
            if not file_exists:
                writer.writerow(REQUEST_LOG_HEADERS)

            # Write the request data
            writer.writerow([
                formatted_timestamp,
                self.request_date,
                self.requestor,
                self.computer_name,
                self.purpose,
                str(self.file_count),
                str(self.total_size),
                file_list_path
            ])

    def format_total_size(self) -> str:
        """Format the total size as a human-readable string"""
        if self.total_size < 1024:
            return f"{self.total_size} B"
        elif self.total_size < 1024*1024:
            return f"{self.total_size/1024:.2f} KB"
        elif self.total_size < 1024*1024*1024:
            return f"{self.total_size/(1024*1024):.2f} MB"
        else:
            return f"{self.total_size/(1024*1024*1024):.2f} GB"