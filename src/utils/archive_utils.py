"""
Archive processing utilities for both transfer logs and requests.
This module provides shared functionality for processing ZIP, TAR, and GZ files.
"""

import os
import zipfile
import tarfile
import gzip
from typing import Union, BinaryIO, Optional, Dict, Callable


class ArchiveProcessor:
    """Utility class for processing various archive formats"""
    
    @staticmethod
    def process_file_with_archives(writer, file_path: str, file_hashes: Optional[Dict[str, str]], 
                                 level: int, container_name: str = "", 
                                 hash_calculator: Optional[Callable] = None):
        """
        Process a file and its archive contents if applicable.
        
        Args:
            writer: CSV writer object
            file_path: Path to the file to process
            file_hashes: Dictionary of pre-calculated file hashes
            level: Current nesting level
            container_name: Name of the containing archive (if any)
            hash_calculator: Optional function to calculate hashes for archive contents
        """
        try:
            # Get file info
            file_size = os.path.getsize(file_path)
            file_hash = file_hashes.get(file_path, "") if file_hashes else ""
            
            # Write the main file entry
            writer.writerow([
                str(level),             # Level
                container_name,         # Container
                file_path,              # FullName (complete path)
                str(file_size),         # Size
                file_hash               # File Hash
            ])
            
            # Check if this is an archive file and process its contents
            file_lower = file_path.lower()
            if file_lower.endswith('.zip'):
                ArchiveProcessor._process_zip_file(writer, file_path, level + 1, 
                                                 file_hashes, file_path, hash_calculator)
            elif file_lower.endswith(('.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz')):
                ArchiveProcessor._process_tar_file(writer, file_path, level + 1, 
                                                 file_hashes, file_path, hash_calculator)
            elif file_lower.endswith('.gz') and not file_lower.endswith('.tar.gz'):
                ArchiveProcessor._process_gz_file(writer, file_path, level + 1, 
                                                file_hashes, file_path, hash_calculator)
                
        except Exception as e:
            # Write error row
            writer.writerow([
                str(level),
                container_name,
                file_path,
                "ERROR",
                f"ERROR: {str(e)}"
            ])

    @staticmethod
    def _process_zip_file(writer, zip_path: Union[str, BinaryIO], level: int,
                         file_hashes: Optional[Dict[str, str]] = None,
                         container_name: Optional[str] = None,
                         hash_calculator: Optional[Callable] = None):
        """Process a ZIP file and write its contents to the writer."""
        if file_hashes is None:
            file_hashes = {}

        try:
            # Always use the provided container name if available
            if container_name:
                current_container = os.path.basename(container_name)
            else:
                current_container = os.path.basename(zip_path) if isinstance(
                    zip_path, str) else "In-Memory ZIP"

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if not file_info.is_dir():
                        # Calculate hash if hash_calculator is provided
                        file_hash = ""
                        if hash_calculator:
                            try:
                                with zip_ref.open(file_info) as archive_file:
                                    file_hash = hash_calculator(archive_file.read())
                            except Exception:
                                file_hash = ""  # Skip hash calculation if it fails
                        
                        # Write the file entry
                        writer.writerow([
                            str(level),
                            current_container,
                            file_info.filename,
                            str(file_info.file_size),
                            file_hash
                        ])

                        # Check if this file is also an archive
                        if file_info.filename.lower().endswith('.zip'):
                            try:
                                with zip_ref.open(file_info) as inner_file:
                                    ArchiveProcessor._process_zip_file(writer, inner_file, level + 1, 
                                                                     file_hashes, file_info.filename, hash_calculator)
                            except Exception:
                                pass  # Skip nested archives if they can't be processed
                        elif file_info.filename.lower().endswith(('.tar', '.tar.gz', '.tgz')):
                            try:
                                with zip_ref.open(file_info) as inner_file:
                                    ArchiveProcessor._process_tar_file(writer, inner_file, level + 1, 
                                                                     file_hashes, file_info.filename, hash_calculator)
                            except Exception:
                                pass  # Skip nested archives if they can't be processed
                    
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing ZIP file {zip_path}: {str(e)}")

    @staticmethod
    def _process_tar_file(writer, tar_path: Union[str, BinaryIO], level: int,
                         file_hashes: Optional[Dict[str, str]] = None,
                         container_name: Optional[str] = None,
                         hash_calculator: Optional[Callable] = None):
        """Process a TAR file and write its contents to the writer."""
        if file_hashes is None:
            file_hashes = {}

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
                    if member.isfile():
                        # Calculate hash if hash_calculator is provided
                        file_hash = ""
                        if hash_calculator:
                            try:
                                extracted_file = tar_ref.extractfile(member)
                                if extracted_file:
                                    file_hash = hash_calculator(extracted_file.read())
                            except Exception:
                                file_hash = ""  # Skip hash calculation if it fails
                        
                        # Write the file entry
                        writer.writerow([
                            str(level),
                            current_container,
                            member.name,
                            str(member.size),
                            file_hash
                        ])

                        # Check if this file is also an archive
                        if member.name.lower().endswith('.zip'):
                            try:
                                inner_file = tar_ref.extractfile(member)
                                if inner_file:
                                    ArchiveProcessor._process_zip_file(writer, inner_file, level + 1, 
                                                                     file_hashes, member.name, hash_calculator)
                            except Exception:
                                pass  # Skip nested archives if they can't be processed
                        elif member.name.lower().endswith(('.tar', '.tar.gz', '.tgz')):
                            try:
                                inner_file = tar_ref.extractfile(member)
                                if inner_file:
                                    ArchiveProcessor._process_tar_file(writer, inner_file, level + 1, 
                                                                     file_hashes, member.name, hash_calculator)
                            except Exception:
                                pass  # Skip nested archives if they can't be processed
                    
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing TAR file {tar_path}: {str(e)}")

    @staticmethod
    def _process_gz_file(writer, gz_path: Union[str, BinaryIO, bytes], level: int,
                        file_hashes: Optional[Dict[str, str]] = None,
                        container_name: Optional[str] = None,
                        hash_calculator: Optional[Callable] = None):
        """Process a GZ file and write its contents to the writer."""
        if file_hashes is None:
            file_hashes = {}

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
                if extracted_name.endswith('.gz'):
                    extracted_name = extracted_name[:-3]

                # Read the content to get size and optionally calculate hash
                content = gz_ref.read()
                content_size = len(content)
                
                # Calculate hash if hash_calculator is provided
                file_hash = ""
                if hash_calculator:
                    try:
                        file_hash = hash_calculator(content)
                    except Exception:
                        file_hash = ""  # Skip hash calculation if it fails

                # Write the extracted file entry
                writer.writerow([
                    str(level),
                    current_container,
                    extracted_name,
                    str(content_size),
                    file_hash
                ])

        except Exception as e:
            # Log error but continue processing
            print(f"Error processing GZ file {gz_path}: {str(e)}")