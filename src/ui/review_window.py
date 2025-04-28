import os
import datetime
import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QPushButton, QSplitter, QTreeWidget,
                               QTreeWidgetItem, QLineEdit, QHeaderView,
                               QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon
from constants import TRANSFER_LOG_HEADERS


class TransferLogReviewerTab(QWidget):
    def __init__(self, config, year=None, parent=None):
        super().__init__(parent)

        # Store reference to parent app for status bar access
        self.app = parent

        # Load configuration
        self.config = config
        self.log_dir = self.config.get(
            "Logging", "OutputFolder", fallback="./logs")

        # Set initial year
        self.selected_year = year or datetime.datetime.now().strftime("%Y")

        # Initialize filtering variables
        self.search_text = ""
        self.filter_field = None
        self.filter_value = None

        # Set up UI
        self._setup_ui()

        # Load available years
        self.load_available_years()

        # Load log file
        self.load_log_file()

    def _setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Year selection
        filter_layout.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox()
        self.year_combo.currentIndexChanged.connect(self.on_year_changed)
        filter_layout.addWidget(self.year_combo)
        
        # Field filter
        filter_layout.addWidget(QLabel("Filter by:"))
        self.field_filter_combo = QComboBox()
        self.field_filter_combo.addItem("-- Select Field --")
        self.field_filter_combo.addItems(TRANSFER_LOG_HEADERS)
        filter_layout.addWidget(self.field_filter_combo)
        
        # Value filter
        self.value_filter_combo = QComboBox()
        self.value_filter_combo.setEditable(True)
        self.value_filter_combo.setMinimumWidth(150)
        filter_layout.addWidget(self.value_filter_combo)
        
        # Apply filter button
        self.apply_filter_btn = QPushButton("Apply Filter")
        self.apply_filter_btn.clicked.connect(self.apply_filter)
        filter_layout.addWidget(self.apply_filter_btn)
        
        # Clear filter button
        self.clear_filter_btn = QPushButton("Clear Filter")
        self.clear_filter_btn.clicked.connect(self.clear_filter)
        filter_layout.addWidget(self.clear_filter_btn)
        
        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.returnPressed.connect(self.apply_search)
        filter_layout.addWidget(self.search_edit)
        
        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.apply_search)
        filter_layout.addWidget(self.search_btn)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # Add refresh and export buttons
        buttons_layout = QHBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Log Data")
        refresh_btn.setIcon(QIcon("resources/icons/refresh.png"))
        refresh_btn.clicked.connect(self.load_log_file)
        buttons_layout.addWidget(refresh_btn)
        
        # Export button
        export_btn = QPushButton("Export Current View")
        export_btn.setIcon(QIcon("resources/icons/export.png"))
        export_btn.clicked.connect(self.export_current_view)
        buttons_layout.addWidget(export_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # Create splitter for top/bottom panes
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        # Top pane: log entries tree
        self.log_tree = QTreeWidget()
        self.log_tree.setHeaderLabels(TRANSFER_LOG_HEADERS)
        self.log_tree.setAlternatingRowColors(True)
        self.log_tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.log_tree.itemSelectionChanged.connect(self.on_log_entry_selected)
        self.log_tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self.log_tree.header().setStretchLastSection(False)
        self.log_tree.header().setMinimumSectionSize(80)
        # Enable sorting
        self.log_tree.setSortingEnabled(True)
        # Initialize with sorting by date (column index typically 0-1)
        self.log_tree.sortByColumn(1, Qt.DescendingOrder)
        splitter.addWidget(self.log_tree)

        # Bottom pane: file details tree
        self.details_tree = QTreeWidget()
        self.details_tree.setHeaderLabels(["File Path", "Size", "Checksum"])
        self.details_tree.setAlternatingRowColors(True)
        self.details_tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self.details_tree.header().setStretchLastSection(False)
        self.details_tree.header().setMinimumSectionSize(40)
        self.details_tree.header().setFirstSectionMovable(True)
        self.details_tree.setSortingEnabled(False)
        splitter.addWidget(self.details_tree)

        # Set initial splitter sizes (30% top, 70% bottom)
        splitter.setSizes([300, 700])

        main_layout.addWidget(splitter)

        # Status bar at bottom of tab
        status_layout = QHBoxLayout()
        self.tab_status_label = QLabel("Ready")
        status_layout.addWidget(self.tab_status_label)
        main_layout.addLayout(status_layout)

    def get_menu_actions(self):
        """Return actions for the menu when this tab is active"""
        actions = []

        # Refresh action
        refresh_action = QAction("&Refresh Log Data", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.load_log_file)
        actions.append(refresh_action)

        # Export action
        export_action = QAction("&Export Current View...", self)
        export_action.triggered.connect(self.export_current_view)
        actions.append(export_action)
        
        # Add separator
        separator = QAction(self)
        separator.setSeparator(True)
        actions.append(separator)
        
        # Reload Configuration
        reload_config_action = QAction("&Reload Configuration", self)
        reload_config_action.setShortcut("Ctrl+R")
        reload_config_action.triggered.connect(self.reload_configuration)
        actions.append(reload_config_action)

        return actions

    def get_toolbar_actions(self):
        """Return actions for the toolbar when this tab is active"""
        return []

    def set_year(self, year):
        """Set the year for log review"""
        # Find the year in the combo box
        index = self.year_combo.findText(year)
        if index >= 0:
            self.year_combo.setCurrentIndex(index)
        else:
            self.app.set_status_message(f"Year {year} not found in logs")

    def load_available_years(self):
        """Load available years from log files"""
        if not os.path.exists(self.log_dir):
            self.app.set_status_message(
                f"Log directory {self.log_dir} not found")
            return

        # Get template from config
        template = self.config.get("Logging", "TransferLogName", fallback="TransferLog_{year}.log")
        
        # Extract the pattern that would represent the year
        # This is a simplified approach - we're just looking for {year} token
        # A more robust approach would parse the template more carefully
        if "{year}" in template:
            prefix = template.split("{year}")[0]
            suffix = template.split("{year}")[1]
            
            # Get list of years to display
            years = []
            try:
                for item in os.listdir(self.log_dir):
                    if item.startswith(prefix) and item.endswith(suffix):
                        # Extract year from filename based on the template pattern
                        year_part = item[len(prefix):len(suffix)]
                        if year_part.isdigit() and len(year_part) == 4:
                            years.append(year_part)

                # Add current year if not already in list
                current_year = datetime.datetime.now().strftime("%Y")
                if current_year not in years:
                    years.append(current_year)

                # Sort years in descending order
                years.sort(reverse=True)

                # Update combo box
                self.year_combo.clear()
                self.year_combo.addItems(years)

                # Set to initially selected year or most recent
                index = self.year_combo.findText(self.selected_year)
                if index >= 0:
                    self.year_combo.setCurrentIndex(index)
                else:
                    self.year_combo.setCurrentIndex(0)

            except Exception as e:
                self.app.set_status_message(
                    f"Error loading available years: {str(e)}")

    def on_year_changed(self):
        """Handle year selection change"""
        self.selected_year = self.year_combo.currentText()
        self.load_log_file()

    def _adjust_column_sizes(self, tree, fullname_column_index=-1):
        """Auto-size columns to fit content once, then make user-resizable"""
        # First set to auto-size
        tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Get auto-sized widths
        widths = [tree.columnWidth(i) for i in range(tree.columnCount())]
        
        # Switch to user-resizable and apply the widths
        tree.header().setSectionResizeMode(QHeaderView.Interactive)
        for i, width in enumerate(widths):
            # Limit fullname column width if specified
            if i == fullname_column_index and fullname_column_index >= 0:
                # Limit FullName column to reasonable width (adjust as needed)
                max_fullname_width = 350
                tree.setColumnWidth(i, min(width, max_fullname_width))
            else:
                tree.setColumnWidth(i, width)

    def load_log_file(self):
        """Load the log file for the selected year"""
        self.log_tree.clear()
        self.details_tree.clear()

        # Temporarily disable sorting for better performance during loading
        self.log_tree.setSortingEnabled(False)

        log_file = os.path.join(self.log_dir, f"TransferLog_{self.selected_year}.log")

        if not os.path.exists(log_file):
            self.app.set_status_message(
                f"Log file for {self.selected_year} not found")
            return

        try:
            with open(log_file, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row

                # Read all rows
                log_entries = list(reader)

                # Apply filters if any
                filtered_entries = self.filter_entries(log_entries)

                # Add entries to tree
                for entry in filtered_entries:
                    item = QTreeWidgetItem(self.log_tree)
                    for i, value in enumerate(entry):
                        # Format total size column (index 10)
                        if i == 10:  # Total Size column
                            formatted_size = format_size(value)
                            item.setText(i, formatted_size)
                            # Store original size for sorting
                            item.setData(i, Qt.UserRole, int(value) if value.isdigit() else 0)
                        else:
                            item.setText(i, value)

                # Update status
                self.app.set_status_message(
                    f"Loaded {len(filtered_entries)} log entries for {self.selected_year}")

        except Exception as e:
            self.app.set_status_message(f"Error loading log file: {str(e)}")
        
        # Re-enable sorting after loading
        self.log_tree.setSortingEnabled(True)
        
        # Auto-size columns for initial display
        self._adjust_column_sizes(self.log_tree)

    def on_log_entry_selected(self):
        """Handle log entry selection"""
        selected_items = self.log_tree.selectedItems()
        if not selected_items:
            return

        # Get the selected item
        item = selected_items[0]

        # Clear details tree
        self.details_tree.clear()

        # Temporarily disable sorting for better performance
        self.details_tree.setSortingEnabled(False)

        # Get file list path (last column)
        file_list_path = item.text(len(TRANSFER_LOG_HEADERS) - 1)

        if not os.path.exists(file_list_path):
            self.app.set_status_message(
                f"File list {file_list_path} not found")
            return

        # Load and display file list
        try:
            with open(file_list_path, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)
                
                # Set the tree headers based on the actual file headers
                self.details_tree.setHeaderLabels(headers)
                
                # Find the indices of special columns
                size_col_index = -1
                fullname_col_index = -1
                for i, header in enumerate(headers):
                    if header.lower() == "size":
                        size_col_index = i
                    elif header.lower() == "fullname":
                        fullname_col_index = i

                # Add data rows
                for row in reader:
                    detail_item = QTreeWidgetItem(self.details_tree)
                    for i, value in enumerate(row):
                        # Format size if we found a size column
                        if i == size_col_index and size_col_index >= 0:
                            formatted_size = format_size(value)
                            detail_item.setText(i, formatted_size)
                            # Store original size for sorting
                            detail_item.setData(i, Qt.UserRole, int(value) if value.isdigit() else 0)
                        else:
                            detail_item.setText(i, value)

            # Update status
            self.app.set_status_message(
                f"Loaded file details from {os.path.basename(file_list_path)}")

        except Exception as e:
            self.app.set_status_message(f"Error loading file list: {str(e)}")
        
        # Auto-size columns for initial display
        self._adjust_column_sizes(self.details_tree, fullname_col_index)

    def apply_filter(self):
        """Apply filter to log entries"""
        field_index = self.field_filter_combo.currentIndex() - \
            1  # -1 because of "Select Field"
        if field_index < 0:
            return

        self.filter_field = field_index
        self.filter_value = self.value_filter_combo.currentText()

        # Reload log with filter applied
        self.load_log_file()

    def clear_filter(self):
        """Clear applied filters"""
        self.filter_field = None
        self.filter_value = None
        self.field_filter_combo.setCurrentIndex(0)
        self.value_filter_combo.setCurrentText("")

        # Reload log without filter
        self.load_log_file()

    def apply_search(self):
        """Apply search to log entries"""
        self.search_text = self.search_edit.text()

        # Reload log with search applied
        self.load_log_file()

    def filter_entries(self, entries):
        """Filter log entries based on filter and search"""
        filtered = entries

        # Apply field/value filter
        if self.filter_field is not None and self.filter_value:
            filtered = [
                e for e in filtered if self.filter_value in e[self.filter_field]]

        # Apply search filter
        if self.search_text:
            text = self.search_text.lower()
            filtered = [e for e in filtered if any(
                text in field.lower() for field in e)]

        return filtered

    def export_current_view(self):
        """Export the currently filtered view to a new CSV file"""
        # Get file name for export
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export Current View", "", "CSV Files (*.csv)")

        if not file_name:
            return

        try:
            log_file = os.path.join(self.log_dir, f"TransferLog_{self.selected_year}.log")

            with open(log_file, 'r', newline='') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Get headers
                log_entries = list(reader)  # Read all data

            # Apply current filters
            filtered_entries = self.filter_entries(log_entries)

            # Write filtered data to export file
            with open(file_name, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)  # Write headers
                writer.writerows(filtered_entries)  # Write filtered data

            self.app.set_status_message(
                f"Exported {len(filtered_entries)} entries to {file_name}")

        except Exception as e:
            self.app.set_status_message(f"Error exporting data: {str(e)}")
    
    def update_log_directory(self):
        """Update log directory from config and refresh data"""
        new_log_dir = self.config.get("Logging", "OutputFolder", fallback="./logs")
        if new_log_dir != self.log_dir:
            self.log_dir = new_log_dir
            self.app.set_status_message(f"Log directory updated to {self.log_dir}")
            self.load_available_years()
            self.load_log_file()
        return self.log_dir

    def reload_configuration(self):
        """Reload configuration from file"""
        try:
            success = self.config.reload()
            if success:
                # Update log directory
                new_log_dir = self.config.get("Logging", "OutputFolder", fallback="./logs")
                old_log_dir = self.log_dir
                
                if new_log_dir != old_log_dir:
                    self.log_dir = new_log_dir
                    self.app.set_status_message(f"Log directory updated to {self.log_dir}")
                    
                    # Reload years list and log data with new directory
                    self.load_available_years()
                    self.load_log_file()
                
                # Show success message
                QMessageBox.information(self, "Configuration Reloaded", 
                                       "Configuration has been successfully reloaded.")
                
                # Notify the main app that config has changed (in case other components need updating)
                if hasattr(self, 'app') and hasattr(self.app, 'on_config_reloaded'):
                    self.app.on_config_reloaded()
            else:
                self.app.set_status_message("Failed to reload configuration")
                QMessageBox.warning(self, "Reload Failed", 
                                   "Failed to reload the configuration file.")
        except Exception as e:
            self.app.set_status_message(f"Error reloading configuration: {str(e)}")
            QMessageBox.critical(self, "Error", 
                                f"Error reloading configuration: {str(e)}")



def format_size(size_bytes):
    """Format a byte size as a human-readable string"""
    try:
        size_bytes = int(size_bytes)
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    except (ValueError, TypeError):
        return size_bytes
