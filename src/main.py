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