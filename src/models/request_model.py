import os
import csv
import datetime
from typing import List, Optional, Dict
from constants import REQUEST_LOG_HEADERS, REQUEST_FILE_LIST_HEADERS
from utils.file_utils import FileInfo, format_filename, get_file_size_str
from utils.file_list_writer import save_file_list_with_progress
from utils.archive_utils import ArchiveProcessor
from models.base_model import BaseLogModel


class RequestLog(BaseLogModel):
    """Class representing a file transfer request"""

    def __init__(self, config, timestamp, request_date, requestor, computer_name,
                 purpose, file_count=0, total_size=0):
        super().__init__(config, timestamp, computer_name, file_count, total_size)
        self.request_dir = self.config.get("Requests", "OutputFolder", fallback="./requests")
        self.request_date = request_date
        self.requestor = requestor
        self.purpose = purpose

    def _save_file_list_with_progress(self, file_list_dir, selected_files, file_hashes, progress_callback, is_canceled_callback):
        """Save the file list CSV with progress reporting"""
        # Get filename template from config
        template = self.config.get("Requests", "FileListName", 
                                  fallback="{date:yyyyMMdd}_{username}_Request_{counter}.csv")
        
        # Prepare data for token replacement
        template_data = {
            'username': self.requestor,
            'computername': self.computer_name,
            'requestor': self.requestor,
            'purpose': self.purpose
        }
        
        # Use shared file list writer
        return save_file_list_with_progress(
            output_dir=file_list_dir,
            files=selected_files,
            file_hashes=file_hashes,
            csv_headers=REQUEST_FILE_LIST_HEADERS,
            filename_template=template,
            template_data=template_data,
            config=self.config,
            progress_callback=progress_callback,
            cancel_check=is_canceled_callback,
            path_formatter=None  # Use default format_display_path
        )

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
