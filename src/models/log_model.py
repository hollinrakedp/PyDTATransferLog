import os
import csv
from typing import List, Optional, Dict
from constants import FILE_LIST_HEADERS
from utils.file_utils import format_filename, format_display_path
from utils.file_list_writer import save_file_list_with_progress
from models.base_model import BaseLogModel


class TransferLog(BaseLogModel):
    """Class representing a transfer log entry"""

    def __init__(self, config, timestamp, transfer_date, username, computer_name,
                 media_type, media_id, transfer_type, source, destination, 
                 request_id="", file_count=0, total_size=0):
        super().__init__(config, timestamp, computer_name, file_count, total_size)
        self.log_dir = self.config.get("Logging", "OutputFolder", fallback="./logs")
        self.delimiter = self.config.get("Logging", "FileDelimiter", fallback="_")
        self.transfer_log_prefix = self.config.get("Logging", "TransferLogPrefix", fallback="DTATransferLog")
        self.file_list_prefix = self.config.get("Logging", "FileListPrefix", fallback="DTAFileList")
        self.transfer_date = transfer_date
        self.username = username
        self.media_type = media_type
        self.media_id = media_id
        self.transfer_type = transfer_type
        self.source = source
        self.destination = destination
        self.request_id = request_id

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

    def _save_file_list(self, log_dir: str, files: List[str],
                        file_hashes: Optional[Dict[str, str]] = None,
                        progress_signal=None, cancel_check=None) -> str:
        """Save detailed file list with archive contents to CSV with optional progress reporting
        
        This method supports both CLI (no progress) and GUI (with progress) usage.
        For CLI usage, simply omit progress_signal and cancel_check parameters.
        """
        # Delegate to the unified method (kept as _save_file_list_with_progress for compatibility)
        return self._save_file_list_with_progress(log_dir, files, file_hashes, progress_signal, cancel_check)

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
