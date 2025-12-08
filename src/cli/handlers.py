import sys
import os
import argparse
import socket
import getpass
import datetime
import csv
from utils.config_manager import ConfigManager
from version import VERSION
from utils.cli_utils import (
    resolve_output_folder,
    collect_files,
    compute_hashes,
    format_timestamp,
)
from models.log_model import TransferLog
from models.request_model import RequestLog
from constants import TRANSFER_LOG_HEADERS

def create_gui_parser():
    """Create the same argument parser used in GUI mode for help extraction"""
    parser = argparse.ArgumentParser(
        description="DTA File Transfer Log",
        epilog="""
For CLI mode help:
  python main.py -t --help    (Transfer logging)
  python main.py -r --help    (File requests)
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-t", "--transfer", action="store_true", help="Transfer Log CLI mode")
    parser.add_argument("-r", "--request", action="store_true", help="Request CLI mode")
    parser.add_argument("--tab", help="Starting tab (0/1/2 or request/log/review)")
    parser.add_argument("-V", "--version", action="version", version=VERSION)
    return parser

def run_cli():
    """Command-line interface entry point"""
    # Store original working directory for CLI output paths
    original_cwd = os.getcwd()

    # Load configuration (change to app directory temporarily)
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        config_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load config from app directory
    config_path = os.path.join(config_dir, "config.ini")
    config = ConfigManager(config_path)

    # Get transfer types from configuration
    transfer_types = config.get_transfer_types()

    # Build a set of all valid options (long and short)
    valid_transfer_types = set(transfer_types.keys()) | set(transfer_types.values())

    parser = argparse.ArgumentParser(description="DTA File Transfer Log CLI")
    parser.add_argument("--media-type", required=True, help="Media type")
    parser.add_argument("--media-id", required=True, help="Media ID")
    parser.add_argument("--transfer-type", required=True, choices=valid_transfer_types,
                        help=f"Transfer type ({', '.join(valid_transfer_types)})")
    parser.add_argument("--source", required=True, help="Source")
    parser.add_argument("--destination", required=True, help="Destination")
    parser.add_argument("--files", nargs="*", default=[], help="Files to log")
    parser.add_argument("--folders", nargs="*", default=[],
                        help="Folders to log (recursively)")
    parser.add_argument("--output", help="Log output folder")
    parser.add_argument("--sha256", action="store_true",
                        help="Include SHA-256 checksums")
    args = parser.parse_args(sys.argv[2:])

    # Collect all files from --files and recursively from --folders
    all_files = collect_files(args.files, args.folders, original_cwd, print)

    if not all_files:
        print("Error: No valid files specified")
        return

    # Handle output folder - CLI args are relative to CWD, config defaults relative to app
    log_output_folder = resolve_output_folder(
        args.output,
        config.get("Logging", "OutputFolder", fallback="./logs"),
        original_cwd,
        config_dir,
    )

    os.makedirs(log_output_folder, exist_ok=True)

    # Create year subfolder for file list logs
    year = datetime.datetime.now().strftime("%Y")
    file_list_dir = os.path.join(log_output_folder, year)
    os.makedirs(file_list_dir, exist_ok=True)

    # Calculate total size of files
    total_size = sum(os.path.getsize(file) for file in all_files if os.path.isfile(file))

    # Create transfer log object
    transfer_log = TransferLog(
        config=config,
        timestamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
        transfer_date=datetime.datetime.now().strftime("%m/%d/%Y"),
        username=getpass.getuser(),
        computer_name=socket.gethostname(),
        media_type=args.media_type,
        media_id=args.media_id,
        transfer_type=args.transfer_type,
        source=args.source,
        destination=args.destination,
        file_count=len(all_files),
        total_size=total_size
    )

    # Calculate file hashes if requested
    file_hashes = {}
    if args.sha256:
        print("Calculating SHA-256 hashes...")
        file_hashes = compute_hashes(all_files, algorithm='sha256', print_fn=print, progress_step=10)

    # Save file list
    print("Generating file list...")
    file_list_path = transfer_log._save_file_list(file_list_dir, all_files, file_hashes)

    if not file_list_path:
        print("Error: Failed to save file list")
        return

    # Create the annual transfer log
    print("Updating transfer log...")
    csv_file = os.path.join(log_output_folder, f"TransferLog_{year}.log")

    # Format timestamp for CSV
    formatted_timestamp = format_timestamp(transfer_log.timestamp)

    # Format transfer data for CSV
    fields = [
        formatted_timestamp,
        transfer_log.transfer_date,
        transfer_log.username,
        transfer_log.computer_name,
        transfer_log.media_type,
        transfer_log.media_id,
        transfer_log.transfer_type,
        transfer_log.source,
        transfer_log.destination,
        "",  # Request ID not applicable in transfer CLI
        str(transfer_log.file_count),
        str(transfer_log.total_size),
        file_list_path
    ]

    # Write CSV entry
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        if not file_exists:
            writer.writerow(TRANSFER_LOG_HEADERS)
        writer.writerow(fields)

    print(f"Transfer log updated: {csv_file}")
    print(f"File list saved: {file_list_path}")
    print(f"Successfully logged {len(all_files)} files")

def run_request_cli():
    """Command-line interface entry point for file transfer requests"""
    # Store original working directory for CLI output paths
    original_cwd = os.getcwd()

    # Load configuration (change to app directory temporarily)
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        config_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load config from app directory
    config_path = os.path.join(config_dir, "config.ini")
    config = ConfigManager(config_path)

    parser = argparse.ArgumentParser(description="DTA File Transfer Request CLI")
    parser.add_argument("--requestor", required=True, help="Name of the person making the request")
    parser.add_argument("--purpose", required=True, help="Purpose/justification for the request")
    parser.add_argument("--request-date", help="Request date (MM/dd/yyyy format, defaults to today)")
    parser.add_argument("--computer-name", help="Computer name (defaults to current hostname)")
    parser.add_argument("--files", nargs="*", default=[], help="Files to include in request")
    parser.add_argument("--folders", nargs="*", default=[],
                        help="Folders to include in request (recursively)")
    parser.add_argument("--output", help="Request output folder")
    parser.add_argument("--sha256", action="store_true",
                        help="Include SHA-256 checksums")

    args = parser.parse_args(sys.argv[2:])

    # Validate and set defaults
    requestor = args.requestor.strip()
    if not requestor:
        print("Error: Requestor name cannot be empty")
        return

    purpose = args.purpose.strip()
    if not purpose:
        print("Error: Purpose cannot be empty")
        return

    # Set request date
    if args.request_date:
        # Validate date format
        try:
            parsed_date = datetime.datetime.strptime(args.request_date, "%m/%d/%Y")
            request_date = args.request_date
        except ValueError:
            print("Error: Request date must be in MM/dd/yyyy format")
            return
    else:
        request_date = datetime.datetime.now().strftime("%m/%d/%Y")

    # Set computer name
    computer_name = args.computer_name if args.computer_name else socket.gethostname()

    # Collect all files from --files and recursively from --folders
    all_files = collect_files(args.files, args.folders, original_cwd, print)

    if not all_files:
        print("Error: No valid files specified")
        return

    # Use output folder from args if provided, otherwise use config
    request_output_folder = resolve_output_folder(
        args.output,
        config.get("Requests", "OutputFolder", fallback="./requests"),
        original_cwd,
        config_dir,
    )
    os.makedirs(request_output_folder, exist_ok=True)

    # Create year subfolder for file list requests
    year = datetime.datetime.now().strftime("%Y")
    file_list_dir = os.path.join(request_output_folder, year)
    os.makedirs(file_list_dir, exist_ok=True)

    # Calculate total size of files
    total_size = sum(os.path.getsize(file) for file in all_files if os.path.isfile(file))

    # Create request log object
    request_log = RequestLog(
        config=config,
        timestamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
        request_date=request_date,
        requestor=requestor,
        computer_name=computer_name,
        purpose=purpose,
        file_count=len(all_files),
        total_size=total_size
    )

    # Calculate file hashes if requested
    file_hashes = {}
    if args.sha256:
        print("Calculating SHA-256 hashes...")
        file_hashes = compute_hashes(all_files, algorithm='sha256', print_fn=print, progress_step=10)

    # Save file list using the request model's method
    print("Generating request file list...")

    # Create a simple progress callback for CLI
    def progress_callback_cli(progress):
        if progress % 10 == 0:  # Print every 10%
            print(f"Progress: {progress}%")

    # Create a simple cancellation callback (never canceled in CLI)
    def is_canceled_callback():
        return False

    # Use a mock progress signal for CLI
    class MockProgressSignal:
        def emit(self, value):
            progress_callback_cli(value)

    mock_progress = MockProgressSignal()

    file_list_path = request_log._save_file_list_with_progress(
        file_list_dir, all_files, file_hashes, mock_progress, is_canceled_callback)

    if not file_list_path:
        print("Error: Failed to save request file list")
        return

    # Create the annual request log if enabled
    enable_request_log = config.get("Requests", "EnableRequestLog", fallback="true").lower() == "true"
    if enable_request_log:
        print("Updating request log...")
        request_log_name = config.get("Requests", "RequestLogName", fallback="RequestLog_{year}.log")
        request_log_name = request_log_name.replace("{year}", year)
        csv_file = os.path.join(request_output_folder, request_log_name)

        # Format timestamp for CSV
        formatted_timestamp = format_timestamp(request_log.timestamp)

        # Write to request log
        request_log._save_request_log(csv_file, formatted_timestamp, file_list_path)
        print(f"Request log updated: {csv_file}")

    print(f"Request file list saved: {file_list_path}")
    print(f"Successfully created request for {len(all_files)} files")
    print(f"Total size: {request_log.format_total_size()}")
