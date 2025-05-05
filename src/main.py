import sys
import os
import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir
from ui.app_window import DTATransferLogApp
from utils.config_manager import ConfigManager

def main():
    """Main application entry point for GUI mode"""
    # Set up working directory to be the location of the script/exe
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        os.chdir(os.path.dirname(sys.executable))
    else:
        # Running as script
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Load configuration
    config = ConfigManager("config.ini")
    
    app = QApplication(sys.argv)
    app.setApplicationName("DTA Transfer Log")
    app.setOrganizationName("DH")
    
    # Load stylesheet based on theme in config
    theme = config.get("UI", "Theme", fallback="")
    if theme:  # Only proceed if a theme was actually specified
        theme_folder = os.path.join("resources", "styles", theme)
        stylesheet_path = os.path.join(theme_folder, f"{theme}.qss")
        
        # Apply the stylesheet if file exists
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, "r") as f:
                stylesheet = f.read()
                #stylesheet = stylesheet.replace("icons/", f"{theme_folder}/icons/")
                
                app.setStyleSheet(stylesheet)
        else:
            print(f"Warning: Theme '{theme}' specified in config.ini was not found.")
    
    # Check command line args for review mode
    parser = argparse.ArgumentParser(description="DTA File Transfer Log")
    parser.add_argument("-r", "--review", action="store_true", help="Open in review mode")
    parser.add_argument("-y", "--year", help="Year to review")
    args, _ = parser.parse_known_args()
    
    # Create the main application window with tabs
    window = DTATransferLogApp(config)
    
    # If review mode specified, switch to review tab
    if args.review:
        window.tab_widget.setCurrentIndex(1)  # Switch to Review tab
        if args.year and hasattr(window.review_tab, 'set_year'):
            window.review_tab.set_year(args.year)
    
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
    args = parser.parse_args()

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

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-c", "--cli"]:
        run_cli()
    else:
        main()