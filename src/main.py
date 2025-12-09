import os
import sys

from cli.handlers import create_gui_parser, run_cli, run_request_cli
from utils.config_manager import ConfigManager


def is_console_available():
    """Check if console output is available"""
    try:
        # Try to get console window handle on Windows
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            return kernel32.GetConsoleWindow() != 0
        else:
            # On other platforms, check if stdout is a TTY
            return sys.stdout.isatty()
    except (AttributeError, OSError):
        return False

def generate_gui_help_content():
    """Generate help content for GUI dialog from argparse parser"""
    import contextlib
    import io

    # Create parser and capture its help output
    parser = create_gui_parser()

    # Capture the help text
    help_buffer = io.StringIO()
    with contextlib.redirect_stdout(help_buffer):
        try:
            parser.print_help()
        except SystemExit:
            pass  # argparse calls sys.exit after print_help

    help_text = help_buffer.getvalue()

    # Add GUI-specific notes at the end
    gui_notes = """

NOTES FOR GUI EXECUTABLE:
    - This GUI executable (dtatransferlog.exe) is optimized for interactive use
    - For command-line operations, use dtatransferlog-cli.exe instead
    - The CLI executable provides full command-line functionality with console output

For detailed documentation, use Help > Documentation from the menu bar."""

    return help_text + gui_notes

def show_gui_help():
    """Show help information in a GUI dialog when console is not available"""
    # Import PySide6 components only when needed for GUI help
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
        QHBoxLayout,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
    )

    # Create a minimal QApplication if one doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create help dialog
    dialog = QDialog()
    dialog.setWindowTitle("PyDTATransferLog Help")
    dialog.setModal(True)
    dialog.resize(700, 500)

    layout = QVBoxLayout()

    # Get help content from actual argparse parser
    help_content = generate_gui_help_content()

    # Text display
    text_edit = QTextEdit()
    text_edit.setPlainText(help_content)
    text_edit.setReadOnly(True)
    text_edit.setFont(QFont("Consolas", 9))  # Monospace font
    layout.addWidget(text_edit)

    # Close button
    button_layout = QHBoxLayout()
    button_layout.addStretch()
    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)
    button_layout.addWidget(close_button)
    layout.addLayout(button_layout)

    dialog.setLayout(layout)
    dialog.exec()

    # Exit after showing help
    sys.exit(0)

def check_for_help_request():
    """Check if help was requested and handle appropriately"""
    # Check for help arguments
    help_args = ['--help', '-h']

    for arg in sys.argv[1:]:
        if arg.lower() in help_args:
            # If we're frozen (executable) and no console available, show GUI help
            if getattr(sys, 'frozen', False) and not is_console_available():
                show_gui_help()
                return True
            # Otherwise, let argparse handle it normally
            break

    return False

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
    # Check for help requests first (before doing anything else)
    if check_for_help_request():
        return

    # Handle --version and -V flags before any imports or directory changes
    if len(sys.argv) > 1 and sys.argv[1] in ["-V", "--version"]:
        from version import VERSION
        print(VERSION)
        return

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

    # Import GUI components only when running in GUI mode
    from PySide6.QtWidgets import QApplication

    from ui.app_window import DTATransferLogApp

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
            with open(stylesheet_path) as f:
                stylesheet = f.read()
                app.setStyleSheet(stylesheet)
        else:
            print(f"Warning: Theme '{theme}' specified in config.ini was not found.")

    # Check command line args for review mode and show help for CLI modes
    parser = create_gui_parser()
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

if __name__ == "__main__":
    main()
