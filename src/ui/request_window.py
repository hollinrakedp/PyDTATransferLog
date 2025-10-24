import datetime
import os
import socket
import subprocess
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton,
                               QDateEdit, QFileDialog, QMessageBox, QListWidget,
                               QSizePolicy, QProgressDialog, QTreeWidget,
                               QTreeWidgetItem, QCheckBox, QGroupBox, QSpacerItem,
                               QTextEdit)
from PySide6.QtCore import Qt, QDate, QThread, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import (QIcon, QAction, QPainter, QPen,
                           QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent)
from utils.file_utils import calculate_file_hash, get_all_files
from models.request_model import RequestLog
from constants import REQUEST_FILE_LIST_HEADERS


class RequestHashWorker(QThread):
    """Worker thread for calculating file hashes for requests"""
    progress = Signal(int)
    finished = Signal(dict)

    def __init__(self, files):
        super().__init__()
        self.files = files
        self.hashes = {}
        self.canceled = False

    def cancel(self):
        """Cancel the hash operation"""
        self.canceled = True

    def run(self):
        total = len(self.files)
        for i, file in enumerate(self.files):
            # Check if canceled
            if self.canceled:
                self.finished.emit({})
                return

            try:
                self.hashes[file] = calculate_file_hash(file)
                self.progress.emit(int((i + 1) / total * 100))
            except Exception as e:
                self.hashes[file] = f"ERROR: {str(e)}"
        self.finished.emit(self.hashes)


class RequestProcessingWorker(QThread):
    """Worker thread for processing request files"""
    progress = Signal(int)
    finished = Signal(str)

    def __init__(self, request_log, files, file_hashes, base_log_dir, file_list_dir):
        super().__init__()
        self.request_log = request_log
        self.files = files
        self.file_hashes = file_hashes
        self.base_log_dir = base_log_dir
        self.file_list_dir = file_list_dir
        self.canceled = False

    def cancel(self):
        """Cancel the request processing operation"""
        self.canceled = True

    def run(self):
        # Check if already canceled
        if self.canceled:
            self.finished.emit("")
            return

        file_list_path = ""
        try:
            # Process the file list
            if not self.canceled:
                file_list_path = self.request_log._save_file_list_with_progress(
                    self.file_list_dir, self.files, self.file_hashes, self.progress,
                    lambda: self.canceled)

            # Delete the file list if canceled
            if self.canceled and file_list_path and os.path.exists(file_list_path):
                try:
                    os.remove(file_list_path)
                    file_list_path = ""
                except Exception as e:
                    print(f"Error deleting file list after cancellation: {str(e)}")

            # Create the annual request log if enabled
            if file_list_path and not self.canceled:
                enable_request_log = self.request_log.config.get("Requests", "EnableRequestLog", fallback="true").lower() == "true"
                if enable_request_log:
                    year = datetime.datetime.now().strftime("%Y")
                    request_log_name = self.request_log.config.get("Requests", "RequestLogName", fallback="RequestLog_{year}.log")
                    request_log_name = request_log_name.replace("{year}", year)
                    csv_file = os.path.join(self.base_log_dir, request_log_name)
                    
                    # Format timestamp for CSV
                    ts = self.request_log.timestamp
                    formatted_timestamp = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
                    
                    # Write to request log
                    self.request_log._save_request_log(csv_file, formatted_timestamp, file_list_path)

        except Exception as e:
            print(f"Error in request processing: {str(e)}")
            file_list_path = ""

        self.finished.emit(file_list_path)


class RequestDropListWidget(QListWidget):
    """Custom QListWidget that accepts drag and drop files"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.DropOnly)

        # Set minimum height to ensure the drop hint is visible
        self.setMinimumHeight(100)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Accept the drag if it contains file URLs or text"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        """Accept the drag movement if it contains file URLs or text"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Process dropped files and folders"""
        mime_data = event.mimeData()

        # Process URLs (files and folders)
        if mime_data.hasUrls():
            self.process_dropped_urls(mime_data.urls())
        # Process text (might be file paths)
        elif mime_data.hasText():
            self.process_dropped_text(mime_data.text())

        event.acceptProposedAction()

    def process_dropped_urls(self, urls):
        """Process dropped URLs"""
        files = []
        folders = []

        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                elif os.path.isdir(file_path):
                    folders.append(file_path)

        # Process all files and folders
        self._process_files_and_folders(files, folders)

    def process_dropped_text(self, text):
        """Process dropped text as potential file paths"""
        paths = text.strip().split('\n')
        files = []
        folders = []

        for path in paths:
            path = path.strip()
            if os.path.isfile(path):
                files.append(path)
            elif os.path.isdir(path):
                folders.append(path)

        # Process all files and folders
        self._process_files_and_folders(files, folders)

    def _process_files_and_folders(self, files, folders):
        """Process lists of files and folders"""
        # Add individual files
        added_count = 0
        for file in files:
            if self.main_window._add_file(file):
                added_count += 1

        # Process folders
        for folder in folders:
            self.main_window.app.set_status_message(f"Scanning folder: {folder}")

            try:
                folder_files = get_all_files(folder)
                for file in folder_files:
                    if self.main_window._add_file(file):
                        added_count += 1
            except Exception as e:
                self.main_window.app.set_status_message(f"Error scanning folder: {str(e)}")

        # Update file count
        self.main_window._update_file_stats()
        self.main_window.app.set_status_message(f"Added {len(files)} files and processed {len(folders)} folders")

    def paintEvent(self, event):
        """Override paint event to show drag-drop hint when empty"""
        super().paintEvent(event)

        # Only show hint when the list is empty
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.save()

            # Draw dashed border
            pen = QPen(Qt.DashLine)
            pen.setColor(Qt.gray)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawRect(5, 5, self.width() - 10, self.height() - 10)

            # Draw hint text
            text = "Drag and drop files or folders here"
            painter.setPen(Qt.gray)
            painter.drawText(self.rect(), Qt.AlignCenter, text)

            painter.restore()


class FileTransferRequestTab(QWidget):
    """Tab for creating file transfer requests"""

    def __init__(self, config, parent=None):
        super().__init__(parent)

        # Store reference to parent app for status bar access
        self.app = parent

        # Load configuration
        self.config = config

        # Initialize variables
        self.selected_files = []
        self.normalized_paths = set()
        self.total_size = 0

        # Set up the UI
        self._setup_ui()

    def _setup_ui(self):
        # Use main layout directly on the widget
        main_layout = QHBoxLayout(self)

        # Create left panel (form inputs)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Set the size policy to prevent horizontal expansion
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # Calculate width based on the longest label
        label_width = 120  # Width for "Computer Name:" plus some padding

        # Request date picker
        date_layout = QHBoxLayout()
        date_label = QLabel("Request Date:")
        date_label.setFixedWidth(label_width)
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_layout.addWidget(date_label)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMaximumDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("MM/dd/yyyy")
        date_layout.addWidget(self.date_edit)
        left_layout.addLayout(date_layout)

        # Requestor field
        requestor_layout = QHBoxLayout()
        requestor_label = QLabel("Requestor:")
        requestor_label.setFixedWidth(label_width)
        requestor_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        requestor_layout.addWidget(requestor_label)
        self.requestor_edit = QLineEdit(os.getlogin())
        requestor_layout.addWidget(self.requestor_edit)
        left_layout.addLayout(requestor_layout)

        # Computer name (read-only)
        comp_layout = QHBoxLayout()
        comp_label = QLabel("Computer Name:")
        comp_label.setFixedWidth(label_width)
        comp_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        comp_layout.addWidget(comp_label)
        self.computer_edit = QLineEdit(socket.gethostname())
        self.computer_edit.setReadOnly(True)
        comp_layout.addWidget(self.computer_edit)
        left_layout.addLayout(comp_layout)

        # Purpose field
        purpose_layout = QHBoxLayout()
        purpose_label = QLabel("Purpose:")
        purpose_label.setFixedWidth(label_width)
        purpose_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        purpose_layout.addWidget(purpose_label)
        self.purpose_edit = QTextEdit()
        self.purpose_edit.setMaximumHeight(80)
        self.purpose_edit.setPlaceholderText("Describe the purpose of this request...")
        purpose_layout.addWidget(self.purpose_edit)
        left_layout.addLayout(purpose_layout)

        # Calculate Checksums checkbox
        checksum_layout = QHBoxLayout()
        checksum_layout.addSpacing(label_width + 5)
        self.include_sha256_check = QCheckBox("Calculate Checksums")
        checksum_layout.addWidget(self.include_sha256_check)
        left_layout.addLayout(checksum_layout)

        # Open Request Log checkbox
        open_log_layout = QHBoxLayout()
        self.open_request_log_check = QCheckBox("Open Request Files")
        open_log_layout.addWidget(self.open_request_log_check)
        left_layout.addLayout(open_log_layout)

        # Add vertical spacer to push all controls to the top
        left_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add left panel to main layout
        main_layout.addWidget(left_panel)

        # Create right panel for file list
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Request output folder display
        request_folder_layout = QHBoxLayout()
        request_folder_layout.addWidget(QLabel("Request Output Folder:"))
        request_output_folder = self.config.get("Requests", "OutputFolder", fallback="./requests")
        self.request_folder_edit = QLineEdit(os.path.abspath(request_output_folder))
        self.request_folder_edit.setReadOnly(True)
        request_folder_layout.addWidget(self.request_folder_edit)

        right_layout.addLayout(request_folder_layout)

        # Buttons for file/folder selection
        button_layout = QHBoxLayout()

        button_width = 120  # Width that accommodates "Remove Selected" with padding
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_selected_files)
        clear_btn.setFixedWidth(button_width)
        clear_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_layout.addWidget(clear_btn)

        remove_selected_btn = QPushButton("Remove Selected")
        remove_selected_btn.clicked.connect(self.remove_selected_file)
        remove_selected_btn.setFixedWidth(button_width)
        remove_selected_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_layout.addWidget(remove_selected_btn)
        
        # Add stretch in the middle to separate the button groups
        button_layout.addStretch()

        add_files_btn = QPushButton("Add Files")
        add_files_btn.clicked.connect(self.select_files)
        add_files_btn.setFixedWidth(button_width)
        add_files_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_layout.addWidget(add_files_btn)

        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.clicked.connect(self.select_folder)
        add_folder_btn.setFixedWidth(button_width)
        add_folder_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_layout.addWidget(add_folder_btn)

        right_layout.addLayout(button_layout)

        # File statistics
        stats_layout = QHBoxLayout()
        self.file_count_label = QLabel("Files: 0")
        self.total_size_label = QLabel("Total Size: 0 B")
        stats_layout.addWidget(self.file_count_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.total_size_label)
        right_layout.addLayout(stats_layout)

        # File list (with drag and drop support)
        self.file_list = RequestDropListWidget(self)
        right_layout.addWidget(self.file_list)

        # Create Request button
        create_layout = QHBoxLayout()
        create_layout.addStretch()
        self.create_request_btn = QPushButton("Create Request")
        self.create_request_btn.clicked.connect(self.create_request)
        # Always enabled (consistent with Log Transfer button)
        create_layout.addWidget(self.create_request_btn)
        right_layout.addLayout(create_layout)

        # Add right panel to main layout
        main_layout.addWidget(right_panel)

        # Update UI state
        self._update_file_stats()

    def get_menu_actions(self):
        """Return menu actions for this tab"""
        actions = []

        # Add Files action
        add_files_action = QAction("&Add Files...", self)
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self.select_files)
        actions.append(add_files_action)

        # Add Folder action
        add_folder_action = QAction("Add &Folder...", self)
        add_folder_action.setShortcut("Ctrl+D")
        add_folder_action.triggered.connect(self.select_folder)
        actions.append(add_folder_action)

        # Clear All action
        clear_action = QAction("&Clear All Files", self)
        clear_action.triggered.connect(self.clear_selected_files)
        actions.append(clear_action)

        # Create Request action
        create_action = QAction("&Create Request...", self)
        create_action.setShortcut("Ctrl+S")
        create_action.triggered.connect(self.create_request)
        # Always enabled - validation happens in create_request method
        actions.append(create_action)

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
        """Return toolbar actions for this tab"""
        # Return empty list - all actions are in the menu
        return []

    def select_files(self):
        """Open file dialog to select files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Request", "", "All Files (*)")
        
        if files:
            added_count = 0
            for file_path in files:
                if self._add_file(file_path):
                    added_count += 1
            
            self._update_file_stats()
            if added_count > 0:
                self.app.set_status_message(f"Added {added_count} files to request")

    def select_folder(self):
        """Open folder dialog to select a folder and add all files"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if folder:
            self.app.set_status_message(f"Scanning folder: {folder}")
            
            try:
                files = get_all_files(folder)
                added_count = 0
                for file_path in files:
                    if self._add_file(file_path):
                        added_count += 1
                
                self._update_file_stats()
                self.app.set_status_message(f"Added {added_count} files from folder")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error scanning folder: {str(e)}")
                self.app.set_status_message("Error scanning folder")

    def _add_file(self, file_path):
        """Add a file to the selected files list"""
        try:
            # Normalize the path for comparison
            normalized_path = self._normalize_path(file_path)
            
            # Check if file already exists in the list
            if normalized_path in self.normalized_paths:
                return False

            # Check if file exists
            if not os.path.isfile(file_path):
                return False

            # Add to lists
            self.selected_files.append(file_path)
            self.normalized_paths.add(normalized_path)
            
            # Add to UI list
            self.file_list.addItem(file_path)
            
            # Update total size
            try:
                self.total_size += os.path.getsize(file_path)
            except:
                pass  # Ignore size calculation errors
            
            return True
        except Exception as e:
            self.app.set_status_message(f"Error adding file {file_path}: {str(e)}")
            return False

    def _normalize_path(self, path):
        """Normalize a path for consistent comparisons"""
        return os.path.normpath(os.path.abspath(path)).lower()

    def remove_selected_file(self):
        """Remove the selected file from the list"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            # Get the file path
            file_path = self.selected_files[current_row]
            
            # Remove from data structures
            self.selected_files.pop(current_row)
            normalized_path = self._normalize_path(file_path)
            self.normalized_paths.discard(normalized_path)
            
            # Update total size
            try:
                self.total_size -= os.path.getsize(file_path)
                if self.total_size < 0:
                    self.total_size = 0
            except:
                pass
            
            # Remove from UI
            self.file_list.takeItem(current_row)
            
            # Update stats
            self._update_file_stats()

    def clear_selected_files(self):
        """Clear all selected files"""
        self.selected_files.clear()
        self.normalized_paths.clear()
        self.total_size = 0
        self.file_list.clear()
        self._update_file_stats()

    def _update_file_stats(self):
        """Update the file count and total size labels"""
        file_count = len(self.selected_files)
        self.file_count_label.setText(f"Files: {file_count}")
        
        # Format total size
        if self.total_size < 1024:
            size_str = f"{self.total_size} B"
        elif self.total_size < 1024*1024:
            size_str = f"{self.total_size/1024:.2f} KB"
        elif self.total_size < 1024*1024*1024:
            size_str = f"{self.total_size/(1024*1024):.2f} MB"
        else:
            size_str = f"{self.total_size/(1024*1024*1024):.2f} GB"
        
        self.total_size_label.setText(f"Total Size: {size_str}")
        
        # Note: Create request button is always enabled (consistent with Log Transfer button)
        # Validation happens when user clicks the button

    def create_request(self):
        """Create the request file(s)"""
        # Collect validation errors
        validation_errors = []

        if not self.selected_files:
            validation_errors.append("No files selected for request")

        requestor = self.requestor_edit.text().strip()
        if not requestor:
            validation_errors.append("Please enter a Requestor name")

        purpose = self.purpose_edit.toPlainText().strip()
        if not purpose:
            validation_errors.append("Please enter a Purpose for the request")

        # Display all validation errors if any
        if validation_errors:
            error_message = "\n• ".join(
                ["Please complete the following required fields:", *validation_errors])
            QMessageBox.warning(
                self, "Missing Required Information", error_message)
            return

        # Get values from form
        request_date = self.date_edit.date().toString("MM/dd/yyyy")
        computer_name = self.computer_edit.text()
        include_sha256 = self.include_sha256_check.isChecked()

        # Get output directory and ensure it exists
        base_request_dir = self.request_folder_edit.text()
        os.makedirs(base_request_dir, exist_ok=True)

        # Create year subfolder for file list
        year = datetime.datetime.now().strftime("%Y")
        file_list_dir = os.path.join(base_request_dir, year)
        os.makedirs(file_list_dir, exist_ok=True)

        # Create request log
        request_log = RequestLog(
            config=self.config,
            timestamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
            request_date=request_date,
            requestor=requestor,
            computer_name=computer_name,
            purpose=purpose,
            file_count=len(self.selected_files),
            total_size=self.total_size
        )

        # Calculate hashes if requested
        if include_sha256:
            self._calculate_hashes(request_log, base_request_dir, file_list_dir)
        else:
            # Skip checksums and proceed directly to file processing
            self._process_request_files(request_log, {}, base_request_dir, file_list_dir)

    def _calculate_hashes(self, request_log, base_request_dir, file_list_dir):
        """Calculate hashes for selected files"""
        if not self.selected_files:
            return

        # Show progress dialog
        progress_dialog = QProgressDialog("Calculating file hashes...", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()

        # Create and start hash worker
        self.hash_worker = RequestHashWorker(self.selected_files)
        self.hash_worker.progress.connect(progress_dialog.setValue)
        self.hash_worker.finished.connect(
            lambda hashes: self._on_hashes_calculated(hashes, request_log, base_request_dir, file_list_dir, progress_dialog)
            if hashes else None
        )
        progress_dialog.canceled.connect(self.hash_worker.cancel)
        
        self.hash_worker.start()

    def _on_hashes_calculated(self, hashes, request_log, base_request_dir, file_list_dir, progress_dialog):
        """Handle hash calculation completion"""
        progress_dialog.close()
        # Now proceed with file processing using the calculated hashes
        self._process_request_files(request_log, hashes, base_request_dir, file_list_dir)

    def _process_request_files(self, request_log, file_hashes, base_request_dir, file_list_dir):
        """Process the request files and create output"""
        # Show progress dialog
        progress_dialog = QProgressDialog("Creating request files...", "Cancel", 0, 100, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()

        # Create and start processing worker
        self.processing_worker = RequestProcessingWorker(
            request_log, self.selected_files, file_hashes, base_request_dir, file_list_dir)
        self.processing_worker.progress.connect(progress_dialog.setValue)
        self.processing_worker.finished.connect(lambda path: self._on_request_created(path, progress_dialog))
        progress_dialog.canceled.connect(self.processing_worker.cancel)
        
        self.processing_worker.start()

        # Keep progress dialog responsive
        while self.processing_worker.isRunning():
            QApplication.processEvents()

    def _on_request_created(self, file_list_path, progress_dialog):
        """Handle request creation completion"""
        progress_dialog.close()
        
        if file_list_path:
            QMessageBox.information(self, "Success", 
                                  f"Request created successfully!\n\nFile list saved to:\n{file_list_path}")
            
            # Open the files if requested
            if self.open_request_log_check.isChecked():
                try:
                    if sys.platform == 'win32':
                        os.startfile(file_list_path)
                    elif sys.platform == 'darwin':  # macOS
                        subprocess.call(['open', file_list_path])
                    else:  # Linux and other Unix-like
                        subprocess.call(['xdg-open', file_list_path])
                except Exception as e:
                    self.app.set_status_message(f"Error opening file: {str(e)}")
                    
            self.app.set_status_message("Request created successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to create request")
            self.app.set_status_message("Request creation failed")

    def reload_configuration(self):
        """Reload configuration from file"""
        try:
            success = self.config.reload()
            if success:
                # Update UI components with new config values
                self.app.set_status_message("Configuration reloaded successfully")
                
                # Update request output folder display
                request_output_folder = self.config.get("Requests", "OutputFolder", fallback="./requests")
                self.request_folder_edit.setText(os.path.abspath(request_output_folder))
                
                # Notify parent app
                if hasattr(self.app, 'on_config_reloaded'):
                    self.app.on_config_reloaded()
            else:
                QMessageBox.warning(self, "Error", "Failed to reload configuration file")
                self.app.set_status_message("Configuration reload failed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reloading configuration: {str(e)}")
            self.app.set_status_message("Configuration reload error")