import os
import csv
import datetime
import io
from dataclasses import dataclass
from typing import List, Optional, Dict, Union, BinaryIO
from constants import FILE_LIST_HEADERS
from utils.file_utils import format_filename


@dataclass
class FileInfo:
    """Class for tracking file information"""
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

    @staticmethod
    def get_container_filename(container_path):
        """Extract just the filename portion of a container path"""
        if not container_path:
            return ""
        return os.path.basename(container_path)

    def process_archive(self, archive_path, level, container_name=None):
        """Process an archive file and get its contents"""
        # When calling process_zip_file, process_tar_file, etc.
        # Use the container filename only
        container_filename = self.get_container_filename(
            container_name or archive_path)


class TransferLog:
    """Class representing a transfer log entry"""

    def __init__(self, config, timestamp, transfer_date, username, computer_name,
                 media_type, media_id, transfer_type, source, destination, 
                 file_count=0, total_size=0):
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
        self.file_count = file_count
        self.total_size = total_size
        self.files: List[FileInfo] = []

    def add_file(self, file_info: FileInfo):
        """Add a file to the transfer log"""
        self.files.append(file_info)
        # Update file count
        self.file_count = len(self.files)

    def save_to_directory(self, directory: str) -> str:
        """Save the transfer log to a file in the specified directory"""
        # Create the log file name
        log_file = f"{self.timestamp}_{self.media_id}_{self.transfer_type}.txt"
        log_path = os.path.join(directory, log_file)

        # Create the file list log file name
        file_list_log = log_path.replace(".txt", "_files.txt")

        # Write the transfer log
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {self.timestamp}\n")
            f.write(f"Transfer Date: {self.transfer_date}\n")
            f.write(f"Username: {self.username}\n")
            f.write(f"Computer Name: {self.computer_name}\n")
            f.write(f"Media Type: {self.media_type}\n")
            f.write(f"Media ID: {self.media_id}\n")
            f.write(f"Transfer Type: {self.transfer_type}\n")
            f.write(f"Source: {self.source}\n")
            f.write(f"Destination: {self.destination}\n")
            f.write(f"File Count: {self.file_count}\n")

        # Write the file list log if there are files
        if self.files:
            with open(file_list_log, "w", encoding="utf-8") as f:
                f.write(
                    f"# File List for Transfer {self.timestamp}_{self.media_id}_{self.transfer_type}\n")
                f.write(
                    f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# Format: Level\tContainer\tFullName\tSize\tSHA256\n")

                # Group files by container (top-level directory)
                containers = {}
                for file_info in self.files:
                    drive, path = os.path.splitdrive(file_info.path)
                    if not drive:
                        # For network paths, get the server and share
                        if path.startswith("\\\\"):
                            parts = path.split("\\")
                            if len(parts) > 2:
                                container = f"\\\\{parts[2]}\\{parts[3]}"
                            else:
                                container = os.path.dirname(file_info.path)
                        else:
                            container = os.path.dirname(file_info.path)
                    else:
                        # For local paths, use the drive
                        container = drive + "\\"

                    if container not in containers:
                        containers[container] = []
                    containers[container].append(file_info)

                # Write files grouped by container
                for container, files in containers.items():
                    for file_info in files:
                        f.write(f"1\t{container}\t{file_info.path}")

                        # Add size if available
                        if file_info.size is not None:
                            f.write(f"\t{file_info.size_str}")
                        else:
                            f.write("\t")

                        # Add SHA-256 if available
                        if file_info.sha256:
                            f.write(f"\t{file_info.sha256}")

                        f.write("\n")

        return log_path

    @classmethod
    def load_from_file(cls, filepath: str) -> 'TransferLog':
        """Load a transfer log from a file"""
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Parse the log header
        data = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        # Create the TransferLog object
        log = cls(
            timestamp=data.get("Timestamp", ""),
            transfer_date=data.get("Transfer Date", ""),
            username=data.get("Username", ""),
            computer_name=data.get("Computer Name", ""),
            media_type=data.get("Media Type", ""),
            media_id=data.get("Media ID", ""),
            transfer_type=data.get("Transfer Type", ""),
            source=data.get("Source", ""),
            destination=data.get("Destination", ""),
            file_count=int(data.get("File Count", "0"))
        )

        # Load the file list if available
        file_list_path = filepath.replace(".txt", "_files.txt")
        if os.path.exists(file_list_path):
            with open(file_list_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines:
                if line.startswith("#") or not line.strip():
                    continue

                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    path = parts[2]
                    sha256 = parts[4] if len(parts) >= 5 else ""

                    # Try to get file size
                    size = None
                    if len(parts) >= 4 and parts[3]:
                        try:
                            size_str = parts[3].lower()
                            if "kb" in size_str:
                                size = float(size_str.replace(
                                    "kb", "").strip()) * 1024
                            elif "mb" in size_str:
                                size = float(size_str.replace(
                                    "mb", "").strip()) * 1024 * 1024
                            elif "gb" in size_str:
                                size = float(size_str.replace(
                                    "gb", "").strip()) * 1024 * 1024 * 1024
                            elif "b" in size_str:
                                size = float(size_str.replace("b", "").strip())
                            else:
                                size = float(size_str)
                        except:
                            size = None

                    log.add_file(FileInfo(path=path, sha256=sha256, size=size))

        return log

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

    def _normalize_path_separators(self, path):
        """Normalize path separators to forward slashes for consistent output"""
        return path.replace('\\', '/')

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

        # Rest of method remains the same
        with open(file_list_path, 'w', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            # Write header
            writer.writerow(["Level", "Container", "FullName", "Size", "FileHash"])

            # Process each file
            for file_path in files:
                if os.path.isfile(file_path):
                    size = os.path.getsize(
                        file_path) if os.path.exists(file_path) else ""
                    checksum = file_hashes.get(
                        file_path, "") if file_hashes else ""

                    # Write entry for the file itself (level 0)
                    writer.writerow([
                        "0",                                        # Level - 0 for regular files
                        "",                                         # Container - empty for regular files
                        self._normalize_path_separators(
                            file_path),                             # Normalized path
                        str(size),                                  # File size
                        checksum                                    # File hash value (if available)
                    ])

                    # Process archives
                    if file_path.lower().endswith('.zip'):
                        self._process_zip_file(
                            writer, file_path, 0, file_hashes)
                    elif file_path.lower().endswith('.tar'):
                        self._process_tar_file(
                            writer, file_path, 0, file_hashes)
                    elif file_path.lower().endswith('.gz'):
                        self._process_gz_file(
                            writer, file_path, 0, file_hashes)

        return file_list_path

    def _save_file_list_with_progress(self, log_dir: str, files: List[str],
                                 file_hashes: Optional[Dict[str, str]] = None,
                                 progress_signal=None, cancel_check=None) -> str:
        """Save detailed file list with archive contents to CSV with progress reporting"""
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

        try:
            with open(file_list_path, 'w', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_ALL)

                # Write header
                writer.writerow(FILE_LIST_HEADERS)

                # Process each file with progress updates
                total_files = len(files)
                for index, file_path in enumerate(files):
                    # Check if operation is canceled
                    if cancel_check and cancel_check():
                        f.close()
                        try:
                            os.remove(file_list_path)
                        except Exception as e:
                            print(
                                f"Error removing partial file on cancel: {str(e)}")
                        return ""

                    if os.path.isfile(file_path):
                        size = os.path.getsize(
                            file_path) if os.path.exists(file_path) else ""
                        checksum = file_hashes.get(
                            file_path, "") if file_hashes else ""

                        # Write entry for the file itself (level 0)
                        writer.writerow([
                            "0",                                         # Level - 0 for regular files
                            "",                                          # Container - empty for regular files
                            self._normalize_path_separators(
                                file_path),  # Normalized path
                            # File size
                            str(size),
                            # SHA256 hash (if available)
                            checksum
                        ])

                        # Process archives
                        if file_path.lower().endswith('.zip'):
                            self._process_zip_file(
                                writer, file_path, 0, file_hashes)
                        elif file_path.lower().endswith('.tar'):
                            self._process_tar_file(
                                writer, file_path, 0, file_hashes)
                        elif file_path.lower().endswith('.gz'):
                            self._process_gz_file(
                                writer, file_path, 0, file_hashes)

                        # Report progress
                        if progress_signal:
                            progress = int((index + 1) / total_files * 100)
                            progress_signal.emit(progress)

            return file_list_path
        except Exception as e:
            print(f"Error in _save_file_list_with_progress: {str(e)}")
            # Clean up partial file if an error occurs
            if os.path.exists(file_list_path):
                try:
                    os.remove(file_list_path)
                except:
                    pass
            return ""

    def _process_zip_file(self, writer, zip_path: Union[str, BinaryIO], level: int,
                          file_hashes: Optional[Dict[str, str]] = None,
                          container_name: Optional[str] = None):
        """Process a ZIP file and write its contents to the log."""
        import zipfile

        try:
            # Always use the provided container name if available
            if container_name:
                current_container = os.path.basename(container_name)
            else:
                current_container = os.path.basename(zip_path) if isinstance(
                    zip_path, str) else "In-Memory ZIP"

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    # Skip directories
                    if file_info.is_dir():
                        continue

                    # Write entry for the file in the archive
                    writer.writerow([
                        str(level + 1),
                        self._normalize_path_separators(current_container),
                        self._normalize_path_separators(file_info.filename),
                        str(file_info.file_size),  # Size
                        ""                      # No hash for archived files
                    ])

                    # Handle nested archives
                    if file_info.filename.lower().endswith('.zip'):
                        with zip_ref.open(file_info.filename) as nested_file:
                            nested_data = io.BytesIO(nested_file.read())
                            self._process_zip_file(
                                writer, nested_data, level + 1, file_hashes, file_info.filename)
                    elif file_info.filename.lower().endswith('.tar'):
                        with zip_ref.open(file_info.filename) as nested_file:
                            nested_data = io.BytesIO(nested_file.read())
                            self._process_tar_file(
                                writer, nested_data, level + 1, file_hashes, file_info.filename)
                    elif file_info.filename.lower().endswith('.gz'):
                        with zip_ref.open(file_info.filename) as nested_file:
                            nested_data = io.BytesIO(nested_file.read())
                            self._process_gz_file(
                                writer, nested_data, level + 1, file_hashes, file_info.filename)
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing ZIP file {zip_path}: {str(e)}")

    def _process_tar_file(self, writer, tar_path: Union[str, BinaryIO], level: int,
                          file_hashes: Optional[Dict[str, str]] = None,
                          container_name: Optional[str] = None):
        """Process a TAR file and write its contents to the log."""
        import tarfile

        try:
            # Use basename for container name
            if container_name:
                current_container = os.path.basename(container_name)
            else:
                current_container = os.path.basename(tar_path) if isinstance(
                    tar_path, str) else "In-Memory TAR"

            # Handle both file paths and file-like objects
            if isinstance(tar_path, str):
                tar_ref = tarfile.open(tar_path, "r:*")
            else:
                tar_ref = tarfile.open(fileobj=tar_path, mode="r:*")

            with tar_ref:
                for member in tar_ref.getmembers():
                    # Skip directories
                    if not member.isfile():
                        continue

                    # Write entry for the file in the archive
                    writer.writerow([
                        str(level + 1),        # Level (increment from parent)
                        current_container,     # Container (the tar file)
                        member.name,           # Filename inside the archive
                        str(member.size),      # Size
                        ""                     # No hash for archived files
                    ])

                    # Handle nested archives
                    if member.name.lower().endswith('.tar'):
                        # Extract nested TAR to memory and process it
                        extracted = tar_ref.extractfile(member)
                        if extracted:
                            nested_data = io.BytesIO(extracted.read())
                            self._process_tar_file(
                                writer, nested_data, level + 1, file_hashes, member.name)
                    elif member.name.lower().endswith('.zip'):
                        # Extract nested ZIP to memory and process it
                        extracted = tar_ref.extractfile(member)
                        if extracted:
                            nested_data = io.BytesIO(extracted.read())
                            self._process_zip_file(
                                writer, nested_data, level + 1, file_hashes, member.name)
                    elif member.name.lower().endswith('.gz'):
                        # Extract nested GZ to memory and process it
                        extracted = tar_ref.extractfile(member)
                        if extracted:
                            nested_data = io.BytesIO(extracted.read())
                            self._process_gz_file(
                                writer, nested_data, level + 1, file_hashes, member.name)
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing TAR file {tar_path}: {str(e)}")

    def _process_gz_file(self, writer, gz_path: Union[str, BinaryIO, bytes], level: int,
                         file_hashes: Optional[Dict[str, str]] = None,
                         container_name: Optional[str] = None):
        """Process a GZ file and write its contents to the log."""
        import gzip

        try:
            # Use basename for container name
            if container_name:
                current_container = os.path.basename(container_name)
            else:
                current_container = os.path.basename(
                    gz_path) if isinstance(gz_path, str) else "In-Memory GZ"

            # Handle both file paths and file-like objects
            if isinstance(gz_path, (str, bytes)):
                gz_ref = gzip.open(gz_path, "rb")
            else:
                # Assume it's already a file-like object
                gz_ref = gzip.GzipFile(fileobj=gz_path, mode="rb")

            with gz_ref:
                # Get the extracted filename by removing the .gz extension
                extracted_name = current_container
                if extracted_name.lower().endswith('.gz'):
                    extracted_name = extracted_name[:-3]

                # Read the content
                content = gz_ref.read()
                content_size = len(content)

                # Write entry for the extracted file
                writer.writerow([
                    str(level + 1),      # Level (increment from parent)
                    current_container,   # Container (the gz file)
                    extracted_name,      # Filename without .gz
                    str(content_size),   # Size of decompressed content
                    ""                   # No hash for archived files
                ])

                # If the extracted file is a TAR file, process it recursively
                if extracted_name.lower().endswith('.tar'):
                    nested_data = io.BytesIO(content)
                    self._process_tar_file(
                        writer, nested_data, level + 1, file_hashes, extracted_name)
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing GZ file {gz_path}: {str(e)}")
