import sys
import os
import argparse
import socket
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir
from ui.app_window import DTATransferLogApp
from utils.config_manager import ConfigManager
from version import VERSION

def parse_tab_argument(tab_arg):
    """Parse tab argument - accepts numbers (0/1/2) or names (case-insensitive)"""
    if tab_arg is None or tab_arg.strip() == "":
        return 0  # Default to Request tab
    
    # Try numeric first
    if tab_arg.isdigit():
        tab_num = int(tab_arg)
        if 0 <= tab_num <= 2:
            return tab_num
    
    # Try name mapping (case-insensitive)
    tab_map = {
        'request': 0,
        'log': 1, 
        'review': 2
    }
    
    normalized_name = tab_arg.lower().strip()
    if normalized_name in tab_map:
        return tab_map[normalized_name]
    
    # Invalid input - show warning and default to Request tab
    print(f"Warning: Invalid tab '{tab_arg}', defaulting to Request tab")
    print("Valid options: 0/1/2 or request/log/review (case-insensitive)")
    return 0  # Default to Request tab

def main():
    """Main application entry point for GUI mode"""
    # Store original working directory before changing it
    original_cwd = os.getcwd()
    
    # Set up working directory to be the location of the script/exe
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        os.chdir(os.path.dirname(sys.executable))
    else:
        # Running as script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Quick check for CLI modes before setting up GUI
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-t", "--transfer"]:
            # Restore original working directory for CLI
            os.chdir(original_cwd)
            run_cli()
            return
        elif sys.argv[1] in ["-r", "--request"]:
            # Restore original working directory for CLI
            os.chdir(original_cwd)
            run_request_cli()
            return

    # Load configuration
    config = ConfigManager("config.ini")
    
    app = QApplication(sys.argv)
    app.setApplicationName("DTA Transfer Log")
    app.setOrganizationName("DH")
    
    # Load stylesheet based on theme in config
    theme = config.get("UI", "Theme", fallback="")
    if theme:  # Only proceed if a theme was actually specified
        if getattr(sys, 'frozen', False):
            # PyInstaller environment
            base_path = sys._MEIPASS
        else:
            # Normal Python environment
            base_path = os.path.dirname(os.path.abspath(__file__))

        theme_folder = os.path.join(base_path, "resources", "styles", theme)
        stylesheet_path = os.path.join(theme_folder, f"{theme}.qss")

        # Apply the stylesheet if file exists
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, "r") as f:
                stylesheet = f.read()
                app.setStyleSheet(stylesheet)
        else:
            print(f"Warning: Theme '{theme}' specified in config.ini was not found.")
    
    # Check command line args for review mode and show help for CLI modes
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
    args = parser.parse_args()
    
    # Create the main application window with tabs
    window = DTATransferLogApp(config)
    
    # Set the starting tab based on --tab argument or config default
    if args.tab:
        tab_index = parse_tab_argument(args.tab)
    else:
        # Check config for default tab
        default_tab = config.get("UI", "DefaultTab", fallback="")
        if default_tab:
            tab_index = parse_tab_argument(default_tab)
        else:
            tab_index = 0  # Default to Request tab if no config setting
    
    window.tab_widget.setCurrentIndex(tab_index)
    
    window.show()
    sys.exit(app.exec())

def run_cli():
    """Command-line interface entry point"""
    # Set up working directory
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        os.chdir(os.path.dirname(sys.executable))
    else:
        # Running as script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
    # Load configuration
    config = ConfigManager("config.ini")
    
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

    # Normalize transfer_type to short name
    if args.transfer_type in transfer_types:
        transfer_type_abbr = transfer_types[args.transfer_type]
    else:
        transfer_type_abbr = args.transfer_type

    # Collect all files from --files and recursively from --folders
    all_files = []
    for file in args.files:
        if os.path.isfile(file):
            all_files.append(os.path.abspath(file))
        else:
            print(f"Warning: File not found: {file}")
    
    for folder in args.folders:
        if os.path.isdir(folder):
            from utils.file_utils import get_all_files
            folder_files = get_all_files(folder)
            all_files.extend(folder_files)
        else:
            print(f"Warning: Directory not found: {folder}")

    if not all_files:
        print("Error: No valid files specified")
        return

    # Create logs with the non-GUI approach
    import datetime
    from models.log_model import TransferLog

    # Use output folder from args if provided, otherwise use config
    log_output_folder = args.output if args.output else config.get("Logging", "OutputFolder", fallback="./logs")
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
        username=os.getlogin(),
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
        from utils.file_utils import calculate_file_hash
        for i, file in enumerate(all_files):
            try:
                file_hashes[file] = calculate_file_hash(file)
                if (i + 1) % 10 == 0 or i + 1 == len(all_files):
                    print(f"Processed {i + 1}/{len(all_files)} files")
            except Exception as e:
                print(f"Error calculating hash for {file}: {str(e)}")
                file_hashes[file] = f"ERROR: {str(e)}"

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
    ts = transfer_log.timestamp
    formatted_timestamp = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"

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
        str(transfer_log.file_count),
        str(transfer_log.total_size),
        file_list_path
    ]

    # Write CSV entry
    from constants import TRANSFER_LOG_HEADERS
    import csv
    
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
    # Store original working directory before changing it
    original_cwd = os.getcwd()
    
    # Set up working directory
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        os.chdir(os.path.dirname(sys.executable))
    else:
        # Running as script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
    # Load configuration
    config = ConfigManager("config.ini")

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
            import datetime as dt
            parsed_date = dt.datetime.strptime(args.request_date, "%m/%d/%Y")
            request_date = args.request_date
        except ValueError:
            print("Error: Request date must be in MM/dd/yyyy format")
            return
    else:
        import datetime as dt
        request_date = dt.datetime.now().strftime("%m/%d/%Y")

    # Set computer name
    computer_name = args.computer_name if args.computer_name else socket.gethostname()

    # Collect all files from --files and recursively from --folders
    # Use original working directory for file resolution
    all_files = []
    for file in args.files:
        # If path is relative, resolve it from original working directory
        if not os.path.isabs(file):
            file = os.path.join(original_cwd, file)
        if os.path.isfile(file):
            all_files.append(os.path.abspath(file))
        else:
            print(f"Warning: File not found: {file}")
    
    for folder in args.folders:
        # If path is relative, resolve it from original working directory
        if not os.path.isabs(folder):
            folder = os.path.join(original_cwd, folder)
        if os.path.isdir(folder):
            from utils.file_utils import get_all_files
            folder_files = get_all_files(folder)
            all_files.extend(folder_files)
        else:
            print(f"Warning: Directory not found: {folder}")

    if not all_files:
        print("Error: No valid files specified")
        return

    # Create requests with the non-GUI approach
    import datetime
    from models.request_model import RequestLog

    # Use output folder from args if provided, otherwise use config
    request_output_folder = args.output if args.output else config.get("Requests", "OutputFolder", fallback="./requests")
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
        from utils.file_utils import calculate_file_hash
        for i, file in enumerate(all_files):
            try:
                file_hashes[file] = calculate_file_hash(file)
                if (i + 1) % 10 == 0 or i + 1 == len(all_files):
                    print(f"Processed {i + 1}/{len(all_files)} files")
            except Exception as e:
                print(f"Error calculating hash for {file}: {str(e)}")
                file_hashes[file] = f"ERROR: {str(e)}"

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
        ts = request_log.timestamp
        formatted_timestamp = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"

        # Write to request log
        request_log._save_request_log(csv_file, formatted_timestamp, file_list_path)
        print(f"Request log updated: {csv_file}")

    print(f"Request file list saved: {file_list_path}")
    print(f"Successfully created request for {len(all_files)} files")
    print(f"Total size: {request_log.format_total_size()}")

if __name__ == "__main__":
    main()