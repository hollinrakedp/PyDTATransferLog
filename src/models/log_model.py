import os
import csv
import datetime
from typing import List, Optional, Dict
from constants import FILE_LIST_HEADERS
from utils.file_utils import FileInfo, format_filename, format_display_path
from utils.file_list_writer import save_file_list_with_progress
from utils.archive_utils import ArchiveProcessor


class TransferLog:
    """Class representing a transfer log entry"""

    def __init__(self, config, timestamp, transfer_date, username, computer_name,
                 media_type, media_id, transfer_type, source, destination, 
                 request_id="", file_count=0, total_size=0):
        self.config = config
        self.log_dir = self.config.get("Logging", "OutputFolder", fallback="./logs")
        self.delimiter = self.config.get("Logging", "FileDelimiter", fallback="_")
        self.transfer_log_prefix = self.config.get("Logging", "TransferLogPrefix", fallback="DTATransferLog")
        self.file_list_prefix = self.config.get("Logging", "FileListPrefix", fallback="DTAFileList")
        self.timestamp = timestamp
        self.transfer_date = transfer_date
        self.username = username
        self.computer_name = computer_name
        self.media_type = media_type
        self.media_id = media_id
        self.transfer_type = transfer_type
        self.source = source
        self.destination = destination
        self.request_id = request_id
        self.file_count = file_count
        self.total_size = total_size
        self.files: List[FileInfo] = []

    def add_file(self, file_info: FileInfo):
        """Add a file to the transfer log"""
        self.files.append(file_info)
        # Update file count
        self.file_count = len(self.files)

    def save(self, log_dir: str, files: List[str], file_hashes: Optional[Dict[str, str]] = None) -> str:
        """Save the transfer log to CSV format with archive processing"""
        # Get the transfer log filename template from config
        template = self.config.get("Logging", "TransferLogName", 
                                  fallback="TransferLog_{year}.log")
        
        # Prepare data for token replacement
        data = {
            'transfertype': self.transfer_type,
            'source': self.source,
            'destination': self.destination,
            'mediatype': self.media_type,
            'mediaid': self.media_id,
            'username': self.username,
            'computername': self.computer_name
        }
        
        # Format the filename using the token system
        log_filename = format_filename(template, data, self.config)
        csv_file = os.path.join(log_dir, log_filename)

        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile(csv_file)

        file_list_path = self._save_file_list(log_dir, files, file_hashes)

        # Format timestamp for CSV
        ts = self.timestamp
        formatted_timestamp = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"

        # Format transfer data for CSV
        fields = [
            formatted_timestamp,
            self.transfer_date,
            self.username,
            self.computer_name,
            self.media_type,
            self.media_id,
            self.transfer_type,
            self.source,
            self.destination,
            str(self.file_count),
            str(self.total_size),
            file_list_path
        ]

        # Write the log entry to the CSV file
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            # Write headers if file is new
            if not file_exists:
                writer.writerow([
                    "Timestamp", "Transfer Date", "Username", "Computer Name",
                    "Media Type", "Media ID", "Transfer Type", "Source",
                    "Destination", "File Count", "Total Size", "File Log"
                ])

            writer.writerow(fields)

        return file_list_path

    def _save_file_list(self, log_dir: str, files: List[str], file_hashes: Optional[Dict[str, str]] = None) -> str:
        """Save detailed file list with archive contents to CSV"""
        # Get filename template from config
        template = self.config.get("Logging", "FileListName", 
                             fallback="{timestamp}_{username}_{transfertype}_{source}-{destination}_FileList.csv")
        
        # Prepare data for token replacement
        data = {
            'transfertype': self.transfer_type,
            'source': self.source,
            'destination': self.destination,
            'mediatype': self.media_type,
            'mediaid': self.media_id,
            'username': self.username,
            'computername': self.computer_name,
            'timestamp': self.timestamp
        }
        
        # Find a unique filename using counter
        counter = 1
        while True:
            file_list_filename = format_filename(template, data, self.config, counter)
            file_list_path = os.path.join(log_dir, file_list_filename)
            if not os.path.exists(file_list_path):
                break
            counter += 1

        normalized_hashes = None
        if file_hashes:
            try:
                normalized_hashes = {
                    os.path.normpath(os.path.abspath(k)): v
                    for k, v in file_hashes.items()
                }
            except Exception:
                normalized_hashes = file_hashes

        with open(file_list_path, 'w', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            # Write header
            writer.writerow(FILE_LIST_HEADERS)

            # Process each file
            for file_path in files:
                if os.path.isfile(file_path):
                    # Process archives using the shared archive processor
                    ArchiveProcessor.process_file_with_archives(
                        writer,
                        format_display_path(file_path),
                        normalized_hashes,
                        0,  # level 0 for top-level files
                        "",  # no container for top-level files
                        None  # no hash calculator for archive contents
                    )

        return file_list_path

    def _save_file_list_with_progress(self, log_dir: str, files: List[str],
                                 file_hashes: Optional[Dict[str, str]] = None,
                                 progress_signal=None, cancel_check=None) -> str:
        """Save detailed file list with archive contents to CSV with progress reporting"""
        # Get filename template from config
        template = self.config.get("Logging", "FileListName", 
                             fallback="{timestamp}_{username}_{transfertype}_{source}-{destination}_FileList.csv")
        
        # Prepare data for token replacement
        template_data = {
            'transfertype': self.transfer_type,
            'source': self.source,
            'destination': self.destination,
            'mediatype': self.media_type,
            'mediaid': self.media_id,
            'username': self.username,
            'computername': self.computer_name,
            'timestamp': self.timestamp
        }
        
        # Use shared file list writer
        return save_file_list_with_progress(
            output_dir=log_dir,
            files=files,
            file_hashes=file_hashes,
            csv_headers=FILE_LIST_HEADERS,
            filename_template=template,
            template_data=template_data,
            config=self.config,
            progress_callback=progress_signal,
            cancel_check=cancel_check,
            path_formatter=format_display_path
        )
