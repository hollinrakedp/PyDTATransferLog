"""
Unified file list writing utility with progress reporting.

This module provides shared functionality for creating detailed file list CSVs
with progress reporting, cancellation support, and archive content inspection.
Used by both TransferLog and RequestLog models.
"""

import csv
import os
from collections.abc import Callable

from utils.archive_utils import ArchiveProcessor
from utils.file_utils import format_display_path, format_filename


def save_file_list_with_progress(
    output_dir: str,
    files: list[str],
    file_hashes: dict[str, str] | None,
    csv_headers: list[str],
    filename_template: str,
    template_data: dict,
    config,
    progress_callback: Callable | None = None,
    cancel_check: Callable | None = None,
    path_formatter: Callable | None = None
) -> str:
    """
    Save a detailed file list CSV with progress reporting and archive processing.

    Args:
        output_dir: Directory where the CSV file will be created
        files: List of file paths to include in the CSV
        file_hashes: Dictionary mapping file paths to their hash values (optional)
        csv_headers: List of column headers for the CSV
        filename_template: Template string for the output filename (with tokens like {counter})
        template_data: Dictionary of data for token replacement in filename
        config: Configuration object for accessing settings
        progress_callback: Optional callback to report progress (0-100)
                          Should have .emit(int) method
        cancel_check: Optional callback that returns True if operation should be canceled
        path_formatter: Optional function to format file paths for display
                       Defaults to format_display_path if None

    Returns:
        str: Path to the created CSV file, or empty string on error/cancellation

    Notes:
        - Uses format_filename() for consistent token replacement
        - Automatically finds next available counter value
        - Processes archive contents using ArchiveProcessor
        - Cleans up partial files on cancellation or error
        - Normalizes file hashes for cross-platform path matching
    """
    # Use default path formatter if none provided
    if path_formatter is None:
        path_formatter = format_display_path

    # Find a unique filename using counter
    counter = 1
    while True:
        file_list_filename = format_filename(
            filename_template,
            template_data,
            config,
            counter
        )
        file_list_path = os.path.join(output_dir, file_list_filename)
        if not os.path.exists(file_list_path):
            break
        counter += 1
        if counter > 999:  # Prevent infinite loop
            file_list_filename = format_filename(
                filename_template,
                template_data,
                config,
                999
            )
            file_list_path = os.path.join(output_dir, file_list_filename)
            break

    try:
        # Prepare normalized hash lookup for cross-platform compatibility
        normalized_hashes = None
        if file_hashes:
            try:
                normalized_hashes = {
                    os.path.normpath(os.path.abspath(k)): v
                    for k, v in file_hashes.items()
                }
            except (OSError, ValueError, TypeError):
                normalized_hashes = file_hashes

        with open(file_list_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)

            # Write headers
            writer.writerow(csv_headers)

            # Process each file with progress updates
            total_files = len(files)
            for index, file_path in enumerate(files):
                # Check if operation is canceled
                if cancel_check and cancel_check():
                    f.close()
                    try:
                        os.remove(file_list_path)
                    except Exception as e:
                        print(f"Error removing partial file on cancel: {e!s}")
                    return ""

                if os.path.isfile(file_path):
                    # Format the path for display
                    display_path = path_formatter(file_path)

                    # Use the shared archive processor
                    ArchiveProcessor.process_file_with_archives(
                        writer,
                        display_path,
                        normalized_hashes,
                        0,  # level 0 for top-level files
                        "",  # no container for top-level files
                        None  # no hash calculator for archive contents
                    )

                    # Report progress
                    if progress_callback:
                        try:
                            progress = int((index + 1) / total_files * 100)
                            if hasattr(progress_callback, 'emit'):
                                progress_callback.emit(progress)
                        except Exception as e:
                            # If progress update fails, just continue
                            print(f"Progress update failed: {str(e)}")

        return file_list_path

    except Exception as e:
        print(f"Error in save_file_list_with_progress: {e!s}")
        # Clean up partial file if an error occurs
        if os.path.exists(file_list_path):
            try:
                os.remove(file_list_path)
            except OSError:
                pass  # File cleanup failed, continue anyway
        return ""
