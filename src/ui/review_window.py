import os
import datetime
import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QComboBox, QPushButton, QSplitter, QTreeWidget,
                               QTreeWidgetItem, QLineEdit, QHeaderView,
                               QFileDialog, QMessageBox, QDateEdit)
from PySide6.QtCore import Qt, QSize, QDate
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

        # Initialize pagination variables
        self.current_page = 1
        self.entries_per_page = 10
        self.all_log_entries = []
        self.filtered_entries = []
        self.total_pages = 1

        # Initialize filtering variables
        self.search_text = ""
        self.filter_field = None
        self.filter_value = None
        self.start_date_filter = None
        self.end_date_filter = None

        # Set up UI
        self._setup_ui()

        # Load log data
        self.load_log_data()

    def _setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Date range filtering
        filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit(QDate.currentDate().addMonths(-1))  # Default to 1 month ago
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("MM/dd/yyyy")
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit(QDate.currentDate())  # Default to today
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("MM/dd/yyyy")
        filter_layout.addWidget(self.end_date)
        
        # Apply date filter button
        self.apply_date_filter_btn = QPushButton("Apply Date Filter")
        self.apply_date_filter_btn.clicked.connect(self.apply_date_filter)
        filter_layout.addWidget(self.apply_date_filter_btn)
        
        # Field filter
        filter_layout.addWidget(QLabel("Filter by:"))
        self.field_filter_combo = QComboBox()
        self.field_filter_combo.addItem("-- Select Field --")
        self.field_filter_combo.addItems(TRANSFER_LOG_HEADERS)
        filter_layout.addWidget(self.field_filter_combo)
        self.field_filter_combo.currentIndexChanged.connect(self.on_filter_field_changed)
        
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
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        pagination_layout.addWidget(QLabel("Page:"))
        self.page_combo = QComboBox()
        pagination_layout.addWidget(self.page_combo)
        
        self.entries_per_page_combo = QComboBox()
        self.entries_per_page_combo.addItems(["5", "10", "25", "50", "All"])
        self.entries_per_page_combo.setCurrentText("10")
        pagination_layout.addWidget(QLabel("Entries per page:"))
        pagination_layout.addWidget(self.entries_per_page_combo)
        self.entries_per_page_combo.currentTextChanged.connect(self.on_page_size_changed)
        
        # Previous/Next page buttons
        self.prev_page_btn = QPushButton("Previous")
        self.prev_page_btn.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_page_btn)
        
        self.next_page_btn = QPushButton("Next")
        self.next_page_btn.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_page_btn)
        
        pagination_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Log Data")
        refresh_btn.setIcon(QIcon("resources/icons/refresh.png"))
        refresh_btn.clicked.connect(self.load_log_data)
        pagination_layout.addWidget(refresh_btn)
        
        # Export button
        export_btn = QPushButton("Export Current View")
        export_btn.setIcon(QIcon("resources/icons/export.png"))
        export_btn.clicked.connect(self.export_current_view)
        pagination_layout.addWidget(export_btn)
        
        main_layout.addLayout(pagination_layout)
        
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

        # Connect field filter change
        self.field_filter_combo.currentIndexChanged.connect(self.on_filter_field_changed)

    def get_menu_actions(self):
        """Return actions for the menu when this tab is active"""
        actions = []

        # Refresh action
        refresh_action = QAction("&Refresh Log Data", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.load_log_data)

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

    def load_log_data(self):
        """Load all log files from the log directory"""
        self.app.set_status_message("Loading log data...")

        # Clear current data
        self.log_tree.clear()
        self.details_tree.clear()
        self.all_log_entries = []

        # Temporarily disable sorting for better performance
        self.log_tree.setSortingEnabled(False)

        if not os.path.exists(self.log_dir):
            self.app.set_status_message(f"Log directory {self.log_dir} not found")
            return
        
        # Find all log files in the directory
        log_files = []
        for file in os.listdir(self.log_dir):
            if file.endswith('.log'):
                log_files.append(os.path.join(self.log_dir, file))
        
        if not log_files:
            self.app.set_status_message("No log files found")
            return

        # Process all log files and collect entries
        for log_file in log_files:
            try:
                with open(log_file, 'r', newline='') as f:
                    reader = csv.reader(f)
                    headers = next(reader)  # Skip header row
                    self.all_log_entries.extend(list(reader))
            except Exception as e:
                self.app.set_status_message(f"Error loading {os.path.basename(log_file)}: {str(e)}")
        
        # Apply filters
        self.apply_filters()
        
        # Re-enable sorting after loading
        self.log_tree.setSortingEnabled(True)

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
        field_index = self.field_filter_combo.currentIndex() - 1
        if field_index < 0:
            return

        self.filter_field = field_index
        self.filter_value = self.value_filter_combo.currentText()

        field_name = TRANSFER_LOG_HEADERS[field_index]
        self.app.set_status_message(f"Filtering by {field_name}: {self.filter_value}")

        # Apply the filter
        self.apply_filters()

    def clear_filter(self):
        """Clear applied filters"""
        self.filter_field = None
        self.filter_value = None
        self.field_filter_combo.setCurrentIndex(0)
        self.value_filter_combo.clear()

        # Reload log without filter
        self.load_log_data()

    def apply_search(self):
        """Apply search to log entries"""
        self.search_text = self.search_edit.text()

        # Reload log with search applied
        self.load_log_data()

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
            # Get column headers from the log tree
            headers = [self.log_tree.headerItem().text(i) for i in range(self.log_tree.columnCount())]

            # Write filtered data to export file
            with open(file_name, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)  # Write headers
                writer.writerows(self.filtered_entries)  # Write filtered data

            self.app.set_status_message(
                f"Exported {len(self.filtered_entries)} entries to {file_name}")

        except Exception as e:
            self.app.set_status_message(f"Error exporting data: {str(e)}")
    
    def update_log_directory(self):
        """Update log directory from config and refresh data"""
        new_log_dir = self.config.get("Logging", "OutputFolder", fallback="./logs")
        if new_log_dir != self.log_dir:
            self.log_dir = new_log_dir
            self.app.set_status_message(f"Log directory updated to {self.log_dir}")
            self.load_log_data()
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
                    
                    # Reload log data with new directory
                    self.load_log_data()
                
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

    def apply_date_filter(self):
        """Apply date range filter"""
        # Get date values
        self.start_date_filter = self.start_date.date()
        self.end_date_filter = self.end_date.date()
        
        # Apply all filters again
        self.apply_filters()

    def apply_filters(self):
        """Apply all filters (date range, field/value, search) to the log entries"""
        filtered = self.all_log_entries
        
        # Apply date range filter
        if self.start_date_filter and self.end_date_filter:
            # Transfer dates are typically in column 1 (index 1) in format MM/DD/YYYY
            filtered = [
                e for e in filtered if self._is_date_in_range(e[1], 
                                                             self.start_date_filter, 
                                                             self.end_date_filter)
            ]
        
        # Apply field/value filter
        if self.filter_field is not None and self.filter_value:
            filtered = [
                e for e in filtered if self.filter_value in e[self.filter_field]]
        
        # Apply search filter
        if self.search_text:
            text = self.search_text.lower()
            filtered = [e for e in filtered if any(
                text in field.lower() for field in e)]

        # Store filtered results
        self.filtered_entries = filtered
        
        # Update pagination
        self._update_pagination()
        
        # Display the current page
        self._display_current_page()
        
        # Update status
        self.app.set_status_message(
            f"Showing {len(self.filtered_entries)} entries ({self.current_page}/{self.total_pages})")

    def _is_date_in_range(self, date_str, start_date, end_date):
        """Check if a date string is within the specified range"""
        try:
            # Convert MM/DD/YYYY to a date object for comparison
            parts = date_str.split('/')
            if len(parts) != 3:
                return False
                
            month, day, year = map(int, parts)
            date = QDate(year, month, day)
            
            return date >= start_date and date <= end_date
        except Exception:
            return False

    def on_page_size_changed(self):
        """Handle change in entries per page"""
        self.entries_per_page = self.entries_per_page_combo.currentText()
        self.current_page = 1  # Reset to first page
        self._update_pagination()
        self._display_current_page()

    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            # Update page combo to match
            self.page_combo.setCurrentText(str(self.current_page))
            self._display_current_page()

    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            # Update page combo to match
            self.page_combo.setCurrentText(str(self.current_page))
            self._display_current_page()

    def _update_pagination(self):
        """Update pagination controls based on filtered entries"""
        if self.entries_per_page == "All":
            self.total_pages = 1
        else:
            entries_per_page = int(self.entries_per_page)
            self.total_pages = max(1, (len(self.filtered_entries) + entries_per_page - 1) // entries_per_page)
        
        # Update page combo box
        self.page_combo.blockSignals(True)
        self.page_combo.clear()
        self.page_combo.addItems([str(i) for i in range(1, self.total_pages + 1)])
        
        # Reset to page 1 or adjust if current page is out of range
        self.current_page = min(self.current_page, self.total_pages)
        if self.current_page < 1:
            self.current_page = 1
            
        # Set current page in combo box
        index = self.page_combo.findText(str(self.current_page))
        if index >= 0:
            self.page_combo.setCurrentIndex(index)
        self.page_combo.blockSignals(False)
        
        # Update previous/next buttons
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)

    def _display_current_page(self):
        """Display the current page of log entries"""
        self.log_tree.clear()
        
        if not self.filtered_entries:
            return
        
        start_idx = 0
        end_idx = len(self.filtered_entries)
        
        if self.entries_per_page != "All":
            entries_per_page = int(self.entries_per_page)
            start_idx = (self.current_page - 1) * entries_per_page
            end_idx = min(start_idx + entries_per_page, len(self.filtered_entries))
        
        # Display the current page of entries
        for entry in self.filtered_entries[start_idx:end_idx]:
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
        
        # Auto-size columns for initial display
        self._adjust_column_sizes(self.log_tree)

    def on_filter_field_changed(self, index):
        """Update value filter options when field selection changes"""
        # Clear the value filter dropdown
        self.value_filter_combo.clear()
        
        if index <= 0:  # "-- Select Field --" option
            return
            
        # Get the selected field index (adjusted for header offset)
        field_index = index - 1
        
        # Collect all unique values for the selected field
        unique_values = set()
        for entry in self.all_log_entries:
            if len(entry) > field_index:
                value = entry[field_index]
                if value:  # Skip empty values
                    unique_values.add(value)
        
        # Update the value filter dropdown
        self.value_filter_combo.addItems(sorted(unique_values))
        
        # Make a nicer status message showing how many values were found
        self.app.set_status_message(f"Found {len(unique_values)} unique values for {TRANSFER_LOG_HEADERS[field_index]}")


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
