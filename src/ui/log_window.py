import datetime
import os
import socket
import sys
import subprocess
import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QDateEdit, QFileDialog, QMessageBox, QListWidget,
                               QSizePolicy, QProgressDialog, QTreeWidget,
                               QTreeWidgetItem, QCheckBox, QGroupBox, QSpacerItem)
from PySide6.QtCore import Qt, QDate, QThread, Signal
from PySide6.QtGui import (QIcon, QAction, QPainter, QPen,
                           QDragEnterEvent, QDragMoveEvent, QDragLeaveEvent, QDropEvent)
from utils.file_utils import calculate_file_hash, get_all_files
from models.log_model import TransferLog
from constants import TRANSFER_LOG_HEADERS


class HashWorker(QThread):
    """Worker thread for calculating file hashes"""
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


class FileProcessingWorker(QThread):
    """Worker thread for processing files and archives"""
    progress = Signal(int)
    finished = Signal(str)

    def __init__(self, transfer_log, files, file_hashes, base_log_dir, file_list_dir):
        super().__init__()
        self.transfer_log = transfer_log
        self.files = files
        self.file_hashes = file_hashes
        self.base_log_dir = base_log_dir
        self.file_list_dir = file_list_dir
        self.canceled = False

    def cancel(self):
        """Cancel the file processing operation"""
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
                file_list_path = self.transfer_log._save_file_list_with_progress(
                    self.file_list_dir, self.files, self.file_hashes, self.progress,
                    lambda: self.canceled)

            # Delete the file list if canceled
            if self.canceled and file_list_path and os.path.exists(file_list_path):
                try:
                    os.remove(file_list_path)
                    file_list_path = ""
                except Exception as e:
                    print(
                        f"Error deleting file list after cancellation: {str(e)}")

            # Create the annual transfer log
            if file_list_path and not self.canceled:
                year = datetime.datetime.now().strftime("%Y")
                csv_file = os.path.join(
                    self.base_log_dir, f"TransferLog_{year}.log")

                # Format timestamp for CSV
                ts = self.transfer_log.timestamp
                formatted_timestamp = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"

                # Format transfer data for CSV
                fields = [
                    formatted_timestamp,
                    self.transfer_log.transfer_date,
                    self.transfer_log.username,
                    self.transfer_log.computer_name,
                    self.transfer_log.media_type,
                    self.transfer_log.media_id,
                    self.transfer_log.transfer_type,
                    self.transfer_log.source,
                    self.transfer_log.destination,
                    str(self.transfer_log.file_count),
                    str(self.transfer_log.total_size),
                    file_list_path
                ]

                # Write the log entry to the CSV file
                file_exists = os.path.isfile(csv_file)
                with open(csv_file, 'a', newline='') as f:
                    writer = csv.writer(f, quoting=csv.QUOTE_ALL)

                    # Write headers if file is new
                    if not file_exists:
                        writer.writerow(TRANSFER_LOG_HEADERS)

                    writer.writerow(fields)

            # Signal completion
            self.finished.emit(file_list_path)

        except Exception as e:
            print(f"Error in file processing worker: {str(e)}")
            # If error occurs and we created a file list, try to delete it
            if file_list_path and os.path.exists(file_list_path):
                try:
                    os.remove(file_list_path)
                except:
                    pass
            self.finished.emit("")


class DragDropFileListWidget(QListWidget):
    """File list widget with drag and drop support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.main_window = parent
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
            self.main_window.app.set_status_message(
                f"Scanning folder: {folder}")

            try:
                folder_files = get_all_files(folder)
                for file in folder_files:
                    if self.main_window._add_file(file):
                        added_count += 1
            except Exception as e:
                self.main_window.app.set_status_message(
                    f"Error scanning folder: {str(e)}")

        # Update file count
        self.main_window._update_file_stats()
        self.main_window.app.set_status_message(
            f"Added {len(files)} files and processed {len(folders)} folders")

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

            # Draw text
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)

            # Draw icon
            icon_text = "📁➕"
            text = "Drag and drop files or folders here"

            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                f"{icon_text}\n\n{text}"
            )

            painter.restore()


class FileTransferLoggerTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)

        # Store reference to parent app for status bar access
        self.app = parent

        # Load configuration
        self.config = config
        self.media_types = self.config.get_list("UI", "MediaTypes")
        self.network_list = self.config.get_list("UI", "NetworkList")
        self.transfer_types = self.config.get_transfer_types()

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

        # Date picker
        date_layout = QHBoxLayout()
        date_label = QLabel("Transfer Date:")
        date_label.setFixedWidth(label_width)
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        date_layout.addWidget(date_label)
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMaximumDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("MM/dd/yyyy")
        date_layout.addWidget(self.date_edit)
        left_layout.addLayout(date_layout)

        # Username (read-only)
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setFixedWidth(label_width)
        username_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        username_layout.addWidget(username_label)
        self.username_edit = QLineEdit(os.getlogin())
        self.username_edit.setReadOnly(True)
        username_layout.addWidget(self.username_edit)
        left_layout.addLayout(username_layout)

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

        # Update helper methods to use consistent label width
        self.label_width = label_width

        # Media Type dropdown
        self.media_type_combo = self._add_combo_field(
            left_layout, "Media Type:", self.media_types)

        # Media ID field
        media_id_prefixes = self.config.get_list("UI", "MediaID")
        self.media_id_edit = self._add_editable_combo_field(left_layout, "Media ID:", media_id_prefixes)

        # Transfer Type dropdown
        self.transfer_type_combo = self._add_combo_field(
            left_layout, "Transfer Type:", list(self.transfer_types.keys()))

        # Source dropdown
        self.source_combo = self._add_combo_field(
            left_layout, "Source:", self.network_list)

        # Destination dropdown
        self.destination_combo = self._add_combo_field(
            left_layout, "Destination:", self.network_list)

        # Calculate Checksums checkbox
        checksum_layout = QHBoxLayout()
        # Add padding to align with fields
        checksum_layout.addSpacing(self.label_width + 5)
        self.include_sha256_check = QCheckBox("Calculate Checksums")
        checksum_layout.addWidget(self.include_sha256_check)
        left_layout.addLayout(checksum_layout)

        # Open Log checkboxes in a group box
        open_logs_group = QGroupBox("Open Logs")
        logs_layout = QHBoxLayout()
        self.open_transfer_log_check = QCheckBox("Transfer Log")
        self.open_file_list_log_check = QCheckBox("File List Log")
        logs_layout.addWidget(self.open_transfer_log_check)
        logs_layout.addWidget(self.open_file_list_log_check)
        open_logs_group.setLayout(logs_layout)
        left_layout.addWidget(open_logs_group)

        # Add vertical spacer to push all controls to the top
        left_layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add left panel to main layout
        main_layout.addWidget(left_panel)

        # Create right panel for file list
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Log output folder display
        log_folder_layout = QHBoxLayout()
        log_folder_layout.addWidget(QLabel("Log Output Folder:"))
        log_output_folder = self.config.get(
            "Logging", "OutputFolder", fallback="./logs")
        self.log_folder_edit = QLineEdit(os.path.abspath(log_output_folder))
        self.log_folder_edit.setReadOnly(True)
        log_folder_layout.addWidget(self.log_folder_edit)

        right_layout.addLayout(log_folder_layout)

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

        select_files_btn = QPushButton("Select Files")
        select_files_btn.clicked.connect(self.select_files)
        select_files_btn.setFixedWidth(button_width)
        select_files_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_layout.addWidget(select_files_btn)

        select_folders_btn = QPushButton("Select Folders")
        select_folders_btn.clicked.connect(self.select_folders)
        select_folders_btn.setFixedWidth(button_width)
        select_folders_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_layout.addWidget(select_folders_btn)

        right_layout.addLayout(button_layout)

        # File listbox
        right_layout.addWidget(QLabel("Selected Files:"))
        self.file_list = DragDropFileListWidget(self)
        self.file_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection)
        right_layout.addWidget(self.file_list)

        # File count and Log Transfer button
        bottom_layout = QHBoxLayout()
        self.file_count_label = QLabel("Files Selected: 0")

        log_transfer_btn = QPushButton("Log Transfer")
        log_transfer_btn.clicked.connect(self.log_transfer)

        bottom_layout.addWidget(self.file_count_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(log_transfer_btn)
        right_layout.addLayout(bottom_layout)

        # Add right panel to main layout
        main_layout.addWidget(right_panel)

    def get_menu_actions(self):
        """Return actions for the menu when this tab is active"""
        actions = []

        # Select Files
        select_files_action = QAction("&Select Files...", self)
        select_files_action.setShortcut("Ctrl+O")
        select_files_action.triggered.connect(self.select_files)
        actions.append(select_files_action)

        # Select Folder
        select_folder_action = QAction("Select &Folder...", self)
        select_folder_action.setShortcut("Ctrl+D")
        select_folder_action.triggered.connect(self.select_folders)
        actions.append(select_folder_action)

        # Log Transfer
        log_action = QAction("&Log Transfer...", self)
        log_action.setShortcut("Ctrl+S")
        log_action.triggered.connect(self.log_transfer)
        actions.append(log_action)

        return actions

    def get_toolbar_actions(self):
        """Return actions for the toolbar when this tab is active"""
        actions = []

        return actions

    def _add_file(self, file_path):
        """Add a file if it's not already in the selection"""
        try:
            normalized_path = self._normalize_path(file_path)
            if normalized_path not in self.normalized_paths:
                try:
                    file_size = os.path.getsize(file_path)
                    self.total_size += file_size
                except Exception:
                    # Handle files with access issues gracefully
                    pass

                self.selected_files.append(file_path)
                self.normalized_paths.add(normalized_path)
                self.file_list.addItem(file_path)
                return True
            return False
        except Exception as e:
            self.app.set_status_message(
                f"Error adding file {file_path}: {str(e)}")
            return False

    def _add_combo_field(self, layout, label_text, options):
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(self.label_width)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        field_layout.addWidget(label)
        combo = QComboBox()
        # Placeholder text instead of empty string
        combo.addItem("-- Select --")
        combo.addItems(options)
        field_layout.addWidget(combo)
        layout.addLayout(field_layout)
        return combo

    def _add_line_field(self, layout, label_text):
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(self.label_width)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        field_layout.addWidget(label)
        line_edit = QLineEdit()
        field_layout.addWidget(line_edit)
        layout.addLayout(field_layout)
        return line_edit

    def _add_editable_combo_field(self, layout, label_text, options):
        """Add an editable combo box field with label"""
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setFixedWidth(self.label_width)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        field_layout.addWidget(label)
        
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItem("")
        
        # Add items to the dropdown
        if options:
            combo.addItems(options)
        
        field_layout.addWidget(combo)
        layout.addLayout(field_layout)
        return combo

    def _normalize_path(self, path):
        """Normalize a path for consistent comparisons"""
        # Convert to absolute path and normalize slashes
        return os.path.normcase(os.path.normpath(os.path.abspath(path)))

    def open_file(self, file_path):
        """Open a file with the default application in a platform-independent way"""
        if os.path.exists(file_path):
            try:
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', file_path])
                else:  # Linux and other Unix-like
                    subprocess.call(['xdg-open', file_path])
            except Exception as e:
                self.app.set_status_message(f"Error opening file: {str(e)}")

    def _format_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024*1024:
            return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024*1024*1024:
            return f"{size_bytes/(1024*1024):.2f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.2f} GB"

    def _update_file_stats(self):
        """Update the file count and size display"""
        size_str = self._format_size(self.total_size)
        self.file_count_label.setText(
            f"Files: {len(self.selected_files)} | Size: {size_str}")

    # Event handlers
    def select_files(self):
        self.app.set_status_message("Selecting files...")
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")

        added_count = 0
        for file in files:
            if self._add_file(file):
                added_count += 1

        self._update_file_stats()
        self.app.set_status_message(f"Added {added_count} files")

    def select_folders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.app.set_status_message(f"Scanning folder: {folder}")

            # Show progress dialog while scanning
            progress = QProgressDialog(
                "Scanning folder...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Scanning Folder")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            try:
                files = get_all_files(folder)
                added_count = 0
                for file in files:
                    if self._add_file(file):
                        added_count += 1

                self._update_file_stats()
                self.app.set_status_message(
                    f"Added {added_count} files from folder")
            finally:
                progress.close()

    def clear_selected_files(self):
        self.selected_files.clear()
        self.normalized_paths.clear()
        self.file_list.clear()
        self.total_size = 0
        self._update_file_stats()
        self.app.set_status_message("Cleared file list")

    def remove_selected_file(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            file_path = item.text()
            if file_path in self.selected_files:
                try:
                    self.total_size -= os.path.getsize(file_path)
                except:
                    pass
                self.selected_files.remove(file_path)
                self.normalized_paths.remove(self._normalize_path(file_path))
                row = self.file_list.row(item)
                self.file_list.takeItem(row)

        self._update_file_stats()
        self.app.set_status_message(f"Removed {len(selected_items)} items")

    def log_transfer(self):
        # Collect validation errors
        validation_errors = []

        if not self.media_id_edit.currentText():
            validation_errors.append("Please enter Media ID")

        if self.media_type_combo.currentIndex() == 0:
            validation_errors.append("Please select Media Type")

        if self.transfer_type_combo.currentIndex() == 0:
            validation_errors.append("Please select Transfer Type")

        if self.source_combo.currentIndex() == 0:
            validation_errors.append("Please select Source")

        if self.destination_combo.currentIndex() == 0:
            validation_errors.append("Please select Destination")

        if not self.selected_files:
            validation_errors.append("No files selected to log")

        # Display all validation errors if any
        if validation_errors:
            error_message = "\n• ".join(
                ["Please complete the following required fields:", *validation_errors])
            QMessageBox.warning(
                self, "Missing Required Information", error_message)
            return

        # Check if source and destination are the same
        source = self.source_combo.currentText()
        destination = self.destination_combo.currentText()

        if source == destination:
            # Show warning dialog with Continue/Cancel options
            reply = QMessageBox.warning(
                self,
                "Source/Destination Match Warning",
                f"Source and Destination are both set to '{source}'. This is highly unusualy.\nDo you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            # Exit if user chooses not to continue
            if reply == QMessageBox.StandardButton.No:
                return

        # Prepare transfer log
        transfer_date = self.date_edit.date().toString("MM/dd/yyyy")
        username = self.username_edit.text()
        computer_name = self.computer_edit.text()
        media_type = self.media_type_combo.currentText()
        media_id = self.media_id_edit.currentText()

        transfer_type_name = self.transfer_type_combo.currentText()
        transfer_type = self.transfer_types.get(transfer_type_name, "")

        # Get the base log directory (OutputFolder) for the transfer log
        base_log_dir = self.log_folder_edit.text()
        
        # Create year subfolder for file list logs
        year = datetime.datetime.now().strftime("%Y")
        file_list_dir = os.path.join(base_log_dir, year)
        os.makedirs(file_list_dir, exist_ok=True)

        # Create transfer log
        transfer_log = TransferLog(
            config=self.config,
            timestamp=datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
            transfer_date=transfer_date,
            username=username,
            computer_name=computer_name,
            media_type=media_type,
            media_id=media_id,
            transfer_type=transfer_type,
            source=source,
            destination=destination,
            file_count=len(self.selected_files),
            total_size=self.total_size
        )

        if self.include_sha256_check.isChecked():
            # Show progress dialog for checksums
            self.progress_dialog = QProgressDialog(
                "Calculating checksums...", "Cancel", 0, 100, self)
            self.progress_dialog.setWindowTitle("Checksums")
            self.progress_dialog.setWindowModality(
                Qt.WindowModality.WindowModal)
            self.progress_dialog.canceled.connect(self.cancel_hash_operation)
            self.progress_dialog.show()

            # Create worker thread for checksums
            self.hash_worker = HashWorker(self.selected_files)
            self.hash_worker.progress.connect(self.progress_dialog.setValue)
            self.hash_worker.finished.connect(
                lambda hashes: self.start_file_processing(
                    transfer_log, hashes, base_log_dir, file_list_dir)
                if hashes else None
            )
            self.hash_worker.start()
        else:
            # Skip checksums and proceed directly to file processing
            self.start_file_processing(transfer_log, {}, base_log_dir, file_list_dir)

    def start_file_processing(self, transfer_log, hashes, base_log_dir, file_list_dir):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

        # Show progress dialog for file processing
        self.file_progress_dialog = QProgressDialog(
            "Processing files and archives...", "Cancel", 0, 100, self)
        self.file_progress_dialog.setWindowTitle("Generating File List")
        self.file_progress_dialog.setWindowModality(
            Qt.WindowModality.WindowModal)
        self.file_progress_dialog.canceled.connect(
            self.cancel_file_processing)
        self.file_progress_dialog.show()

        # Create worker thread for file processing
        self.file_worker = FileProcessingWorker(
            transfer_log, self.selected_files, hashes, base_log_dir, file_list_dir)
        self.file_worker.progress.connect(self.file_progress_dialog.setValue)
        self.file_worker.finished.connect(lambda file_path: self.complete_log_save(
            transfer_log, file_path))
        self.file_worker.start()

    def complete_log_save(self, transfer_log, file_path):
        # Close progress dialog
        if hasattr(self, 'file_progress_dialog'):
            self.file_progress_dialog.close()

        # Check if this was a cancellation
        if not file_path and hasattr(self, 'file_worker') and self.file_worker.canceled:
            self.app.set_status_message("Log generation cancelled by user")
            return

        if file_path:
            # Success message box
            QMessageBox.information(
                self,
                "Success",
                f"Transfer log saved successfully to yearly CSV file.\n"
                f"File list saved as CSV."
            )

            # Success status bar
            self.app.set_status_message(
                f"Logs generated successfully - {len(self.selected_files)} files processed")

            # Open log files if requested
            if self.open_file_list_log_check.isChecked():
                self.open_file(file_path)

            if self.open_transfer_log_check.isChecked():
                year = datetime.datetime.now().strftime("%Y")
                yearly_log = os.path.join(self.log_folder_edit.text(), f"TransferLog_{year}.log")
                self.open_file(yearly_log)
        else:
            QMessageBox.critical(self, "Error", "Failed to save log file")
            self.app.set_status_message("Error: Failed to save log file")

    def cancel_hash_operation(self):
        """Cancel the hash calculation operation and entire logging process"""
        if hasattr(self, 'hash_worker'):
            self.hash_worker.cancel()
            self.app.set_status_message("Log generation canceled by user")

        # Close the progress dialog if it's open
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

    def cancel_file_processing(self):
        """Cancel the file processing operation"""
        if hasattr(self, 'file_worker'):
            self.file_worker.cancel()
            self.app.set_status_message("File processing canceled by user")

        # Close the progress dialog if it's open
        if hasattr(self, 'file_progress_dialog'):
            self.file_progress_dialog.close()
