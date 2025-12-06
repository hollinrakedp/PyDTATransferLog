from typing import List
from utils.file_utils import FileInfo, get_file_size_str

class BaseLogModel:
    """Base class for transfer and request logs"""

    def __init__(self, config, timestamp, computer_name, file_count=0, total_size=0):
        self.config = config
        self.timestamp = timestamp
        self.computer_name = computer_name
        self.file_count = file_count
        self.total_size = total_size
        self.files: List[FileInfo] = []

    def add_file(self, file_info: FileInfo):
        """Add a file to the log"""
        self.files.append(file_info)
        # Update file count
        self.file_count = len(self.files)

    def format_total_size(self) -> str:
        """Format the total size as a human-readable string"""
        return get_file_size_str(self.total_size)
