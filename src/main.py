import sys
import os
import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir
from ui.main_window import FileTransferLoggerWindow
from ui.review_window import TransferLogReviewerWindow
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
    
    # Load stylesheet if it exists
    stylesheet_path = os.path.join("resources", "styles", "main.qss")
    if os.path.exists(stylesheet_path):
        with open(stylesheet_path, "r") as f:
            app.setStyleSheet(f.read())
    
    # Check command line args for review mode
    parser = argparse.ArgumentParser(description="DTA File Transfer Log")
    parser.add_argument("-r", "--review", action="store_true", help="Open in review mode")
    parser.add_argument("-y", "--year", help="Year to review")
    args, _ = parser.parse_known_args()
    
    if args.review:
        window = TransferLogReviewerWindow(year=args.year)
    else:
        window = FileTransferLoggerWindow(config)
    
    window.show()
    sys.exit(app.exec())

def run_cli():
    """Command-line interface entry point"""
    # Parse arguments for CLI mode
    parser = argparse.ArgumentParser(description="DTA File Transfer Log CLI")
    # Add arguments similar to original
    args = parser.parse_args()
    # Process CLI commands

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["-c", "--cli"]:
        run_cli()
    else:
        main()