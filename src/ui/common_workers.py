"""
Unified worker threads for UI operations.

This module provides reusable QThread workers that can be used across different
UI components (log_window.py and request_window.py).
"""

import datetime
import os
import csv
from PySide6.QtCore import QThread, Signal
from utils.file_utils import calculate_file_hash
from constants import TRANSFER_LOG_HEADERS


class FileHashWorker(QThread):
    """
    Worker thread for calculating file hashes.
    
    This worker can be used by any UI component that needs to calculate
    SHA-256 hashes for a list of files with progress reporting.
    
    Signals:
        progress: Emits progress percentage (0-100)
        finished: Emits dictionary mapping file paths to hash values
    """
    progress = Signal(int)
    finished = Signal(dict)

    def __init__(self, files):
        """
        Initialize the hash worker.
        
        Args:
            files: List of file paths to calculate hashes for
        """
        super().__init__()
        self.files = files
        self.hashes = {}
        self.canceled = False

    def cancel(self):
        """Cancel the hash operation"""
        self.canceled = True

    def run(self):
        """Calculate hashes for all files with progress reporting"""
        total = len(self.files)
        for i, file in enumerate(self.files):
            # Check if canceled
            if self.canceled:
                self.finished.emit({})
                return

            try:
                self.hashes[file] = calculate_file_hash(file)
                self.progress.emit(int((i + 1) / total * 100))
            except Exception as e:
                self.hashes[file] = f"ERROR: {str(e)}"
        
        self.finished.emit(self.hashes)


class FileProcessingWorker(QThread):
    """
    Worker thread for processing files and creating log/request entries.
    
    This worker uses dependency injection to work with different model types
    (TransferLog, RequestLog).
    The model must implement:
        - _save_file_list_with_progress(dir, files, hashes, progress_callback, cancel_check)
        - Properties: timestamp, and model-specific fields
    
    The save_callback function handles model-specific annual log creation.
    
    Signals:
        progress: Emits progress percentage (0-100)
        finished: Emits the file list path (empty string on error/cancel)
    """
    progress = Signal(int)
    finished = Signal(str)

    def __init__(self, model, files, file_hashes, base_log_dir, file_list_dir, 
                 save_callback=None):
        """
        Initialize the file processing worker.
        
        Args:
            model: TransferLog or RequestLog instance
            files: List of file paths to process
            file_hashes: Dictionary mapping file paths to hash values
            base_log_dir: Base directory for transfer log files
            file_list_dir: Directory for detailed file list CSV
            save_callback: Optional function to call for saving transfer log entry
                          Signature: callback(base_log_dir, formatted_timestamp, file_list_path)
                          If None, no transfer log is created (supports both models)
        """
        super().__init__()
        self.model = model
        self.files = files
        self.file_hashes = file_hashes
        self.base_log_dir = base_log_dir
        self.file_list_dir = file_list_dir
        self.save_callback = save_callback
        self.canceled = False

    def cancel(self):
        """Cancel the file processing operation"""
        self.canceled = True

    def run(self):
        """Process files and create log entries with progress reporting"""
        # Check if already canceled
        if self.canceled:
            self.finished.emit("")
            return

        file_list_path = ""
        try:
            # Process the file list
            if not self.canceled:
                file_list_path = self.model._save_file_list_with_progress(
                    self.file_list_dir, 
                    self.files, 
                    self.file_hashes, 
                    self.progress,
                    lambda: self.canceled
                )

            # Delete the file list if canceled
            if self.canceled and file_list_path and os.path.exists(file_list_path):
                try:
                    os.remove(file_list_path)
                    file_list_path = ""
                except Exception as e:
                    print(f"Error deleting file list after cancellation: {str(e)}")

            # Create the transfer log entry if not canceled and callback provided
            if file_list_path and not self.canceled and self.save_callback:
                # Format timestamp for CSV
                ts = self.model.timestamp
                formatted_timestamp = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
                
                # Call the model-specific save callback
                self.save_callback(
                    self.base_log_dir, 
                    formatted_timestamp, 
                    file_list_path
                )

            # Signal completion
            self.finished.emit(file_list_path)

        except Exception as e:
            print(f"Error in file processing worker: {str(e)}")
            # If error occurs and we created a file list, try to delete it
            if file_list_path and os.path.exists(file_list_path):
                try:
                    os.remove(file_list_path)
                except OSError:
                    pass  # File cleanup failed, continue anyway
            self.finished.emit("")
