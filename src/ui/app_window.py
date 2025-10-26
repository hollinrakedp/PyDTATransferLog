import os
import sys
import datetime
from PySide6.QtWidgets import (QMainWindow, QTabWidget, QMessageBox)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt
from ui.log_window import FileTransferLoggerTab
from ui.review_window import TransferLogReviewerTab
from ui.request_window import FileTransferRequestTab
from version import VERSION


class DTATransferLogApp(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("DTA File Transfer Log")

        # Load configuration
        self.config = config

        # Determine the base path (for PyInstaller or Normal)
        if getattr(sys, 'frozen', False):
            # PyInstaller Bundle
            base_path = sys._MEIPASS  # Access the temp directory PyInstaller uses
            icon_path = os.path.join(base_path, "resources", "icons", "dtatransferlog.png")
        else:
            # Normal Execution
            icon_path = os.path.join("resources", "icons", "dtatransferlog.png")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Warning: Window icon not found at {icon_path}")

        # Set up UI
        self._setup_ui()

    def _setup_ui(self):
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create request tab (first)
        self.request_tab = FileTransferRequestTab(self.config, self)
        self.tab_widget.addTab(self.request_tab, "Request")

        # Create log tab (second)
        self.log_tab = FileTransferLoggerTab(self.config, self)
        self.tab_widget.addTab(self.log_tab, "Log")

        # Create review tab (third)
        self.review_tab = TransferLogReviewerTab(self.config, parent=self)
        self.tab_widget.addTab(self.review_tab, "Review")

        # Set up menu and toolbar
        self._setup_menu()
        self._setup_toolbar()

        # Connect tab changed signal to update menu and toolbar
        self.tab_widget.currentChanged.connect(self._update_menu)
        self.tab_widget.currentChanged.connect(self._update_toolbar)

        # Connect tab changed signal to refresh data when switching to review tab
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Initialize menu with actions from the initial tab (index 0)
        self._update_menu(0)
        self._update_toolbar(0)

        # Set reasonable initial size
        self.resize(1000, 700)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _setup_menu(self):
        """Set up the menu bar"""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        # Add actions for the current tab
        self.tab_widget.currentChanged.connect(self._update_menu)

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        self.tools_menu = menu_bar.addMenu("&Tools")

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        # About action
        about_action = QAction("&About...", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Set up the toolbar"""
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setMovable(False)

        # Actions will be updated based on the current tab
        self.tab_widget.currentChanged.connect(self._update_toolbar)

    def _update_menu(self, index):
        """Update menu based on the active tab"""
        # Clear dynamic menus
        self.tools_menu.clear()

        # Add tab-specific actions
        if index == 0:  # Request tab
            if hasattr(self.request_tab, 'get_menu_actions'):
                actions = self.request_tab.get_menu_actions()
                for action in actions:
                    self.tools_menu.addAction(action)
        elif index == 1:  # Log tab
            if hasattr(self.log_tab, 'get_menu_actions'):
                actions = self.log_tab.get_menu_actions()
                for action in actions:
                    self.tools_menu.addAction(action)
        else:  # Review tab
            if hasattr(self.review_tab, 'get_menu_actions'):
                actions = self.review_tab.get_menu_actions()
                for action in actions:
                    self.tools_menu.addAction(action)

    def _update_toolbar(self, index):
        """Update toolbar based on the active tab"""
        # Clear toolbar
        self.toolbar.clear()

        # Add tab-specific toolbar items
        if index == 0:  # Request tab
            if hasattr(self.request_tab, 'get_toolbar_actions'):
                actions = self.request_tab.get_toolbar_actions()
                for action in actions:
                    self.toolbar.addAction(action)
        elif index == 1:  # Log tab
            if hasattr(self.log_tab, 'get_toolbar_actions'):
                actions = self.log_tab.get_toolbar_actions()
                for action in actions:
                    self.toolbar.addAction(action)
        else:  # Review tab
            if hasattr(self.review_tab, 'get_toolbar_actions'):
                actions = self.review_tab.get_toolbar_actions()
                for action in actions:
                    self.toolbar.addAction(action)

    def show_about(self):
        """Display information about the application"""
        about_text = f"""
        <h2>DTA File Transfer Log</h2>
        <p>© 2025 Darren Hollinrake</p>
        <p>Licensed under the MIT License.</p>
        <p>Version {VERSION}</p>
        """

        QMessageBox.about(self, "About DTA File Transfer Log", about_text)

    def set_status_message(self, message):
        """Set a message in the status bar"""
        self.statusBar().showMessage(message)

    def _on_tab_changed(self, index):
        """Handle tab change events"""
        if index == 2:  # Review tab (now index 2 because Request is at index 1)
            # Refresh log data when switching to review tab
            self.set_status_message("Refreshing log data...")
            self.review_tab.load_log_data()

    def on_config_reloaded(self):
        """Notify all tabs that configuration has been reloaded"""
        # Update review tab
        if hasattr(self, 'review_tab'):
            self.review_tab.update_log_directory()
        self.set_status_message("All tabs updated with new configuration")
