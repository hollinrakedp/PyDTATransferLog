import os
import socket
import datetime
import csv
import sys
import subprocess
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QComboBox, QPushButton,
                               QListWidget, QCheckBox, QFileDialog, QMessageBox,
                               QDateEdit, QProgressDialog, QStatusBar, QSizePolicy,
                               QSpacerItem, QGroupBox)
from PySide6.QtCore import Qt, QDate, QThread, Signal, QMimeData, QUrl
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QPainter, QPen
from utils.config_manager import ConfigManager
from utils.file_utils import get_all_files, calculate_file_hash
from models.log_model import TransferLog, FileInfo


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

    def __init__(self, transfer_log, files, file_hashes, log_dir):
        super().__init__()
        self.transfer_log = transfer_log
        self.files = files
        self.file_hashes = file_hashes
        self.log_dir = log_dir
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
                    self.log_dir, self.files, self.file_hashes, self.progress,
                    lambda: self.canceled)

            # Delete the file list if canceled
            if self.canceled and file_list_path and os.path.exists(file_list_path):
                try:
                    os.remove(file_list_path)
                    file_list_path = ""
                except Exception as e:
                    print(f"Error deleting file list after cancellation: {str(e)}")

            # Create the annual transfer log
            if file_list_path and not self.canceled:
                year = datetime.datetime.now().strftime("%Y")
                csv_file = os.path.join(
                    self.log_dir, f"TransferLog_{year}.log")

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
                        writer.writerow([
                            "Timestamp", "Transfer Date", "Username", "Computer Name",
                            "Media Type", "Media ID", "Transfer Type", "Source",
                            "Destination", "File Count", "Total Size", "File Log"
                        ])

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

        # Add files to the selection
        for file in files:
            normalized_path = self.main_window._normalize_path(file)
            if normalized_path not in [self.main_window._normalize_path(f) for f in self.main_window.selected_files]:
                file_size = os.path.getsize(file)
                self.main_window.total_size += file_size
                self.main_window.selected_files.append(file)
                self.addItem(file)
        
        # Update display with file count and total size
        self.main_window._update_file_stats()

        # Process folders
        for folder in folders:
            self.main_window.statusBar().showMessage(
                f"Scanning folder: {folder}")

            try:
                folder_files = get_all_files(folder)
                for file in folder_files:
                    normalized_path = self.main_window._normalize_path(file)
                    if normalized_path not in [self.main_window._normalize_path(f) for f in self.main_window.selected_files]:
                        self.main_window.selected_files.append(file)
                        self.addItem(file)
            except Exception as e:
                self.main_window.statusBar().showMessage(
                    f"Error scanning folder: {str(e)}")

        # Update file count
        self.main_window._update_file_stats()
        self.main_window.statusBar().showMessage(
            f"Added {len(files)} files and processed {len(folders)} folders")

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

        # Add files to the selection
        for file in files:
            normalized_path = self.main_window._normalize_path(file)
            if normalized_path not in [self.main_window._normalize_path(f) for f in self.main_window.selected_files]:
                try:
                    self.main_window.total_size += os.path.getsize(file)
                except:
                    pass
                self.main_window.selected_files.append(file)
                self.addItem(file)

        # Process folders
        for folder in folders:
            try:
                folder_files = get_all_files(folder)
                for file in folder_files:
                    normalized_path = self.main_window._normalize_path(file)
                    if normalized_path not in [self.main_window._normalize_path(f) for f in self.main_window.selected_files]:
                        self.main_window.selected_files.append(file)
                        self.addItem(file)
            except Exception as e:
                self.main_window.statusBar().showMessage(
                    f"Error scanning folder: {str(e)}")

        # Update file count
        self.main_window._update_file_stats()
        self.main_window.statusBar().showMessage(
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


class FileTransferLoggerWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("DTA File Transfer Log")

        # Load configuration
        self.config = config
        self.media_types = self.config.get_list("UI", "MediaTypes")
        self.network_list = self.config.get_list("UI", "NetworkList") 
        self.transfer_types = self.config.get_transfer_types()

        # Set up icon
        icon_path = os.path.join("resources", "icons", "dtatransferlog.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Initialize variables
        self.selected_files = []
        self.total_size = 0

        # Set up the UI
        self._setup_ui()

    def _setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

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
        self.media_id_edit = self._add_line_field(left_layout, "Media ID:")
        
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

        # Add the left panel to the main layout
        main_layout.addWidget(left_panel)

        # Create right panel (file list)
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

        # Browse button
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_log_folder)
        log_folder_layout.addWidget(browse_btn)

        right_layout.addLayout(log_folder_layout)

        # Buttons for file/folder selection
        button_layout = QHBoxLayout()

        select_files_btn = QPushButton("Select Files")
        select_files_btn.clicked.connect(self.select_files)
        button_layout.addWidget(select_files_btn)

        select_folders_btn = QPushButton("Select Folders")
        select_folders_btn.clicked.connect(self.select_folders)
        button_layout.addWidget(select_folders_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_selected_files)
        button_layout.addWidget(clear_btn)

        remove_selected_btn = QPushButton("Remove Selected")
        remove_selected_btn.clicked.connect(self.remove_selected_file)
        button_layout.addWidget(remove_selected_btn)

        right_layout.addLayout(button_layout)

        # File listbox
        right_layout.addWidget(QLabel("Selected Files:"))
        self.file_list = DragDropFileListWidget(self)
        self.file_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection)
        right_layout.addWidget(self.file_list)

        # File count and Generate logs button
        bottom_layout = QHBoxLayout()
        self.file_count_label = QLabel("Files Selected: 0")

        generate_logs_btn = QPushButton("Generate Logs")
        generate_logs_btn.clicked.connect(self.save_logs)

        bottom_layout.addWidget(self.file_count_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(generate_logs_btn)
        right_layout.addLayout(bottom_layout)

        # Add the right panel to the main layout
        main_layout.addWidget(right_panel)

        # Set a reasonable initial size
        self.resize(900, 600)

        # Status bar
        self.statusBar().showMessage("Ready")

    # Helper methods
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
                self.statusBar().showMessage(f"Error opening file: {str(e)}")

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
        self.file_count_label.setText(f"Files: {len(self.selected_files)} | Size: {size_str}")

    # Event handlers
    def browse_log_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Log Output Folder", self.log_folder_edit.text())
        if folder:
            self.log_folder_edit.setText(folder)
            self.config.set("Logging", "OutputFolder", folder)
            self.config.save()

    def select_files(self):
        self.statusBar().showMessage("Selecting files...")
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files")

        added_count = 0
        for file in files:
            normalized_path = self._normalize_path(file)
            # Check if normalized path is already in selected files
            if normalized_path not in [self._normalize_path(f) for f in self.selected_files]:
                try:
                    self.total_size += os.path.getsize(file)
                except:
                    pass
                self.selected_files.append(file)
                self.file_list.addItem(file)
                added_count += 1

        self._update_file_stats()
        self.statusBar().showMessage(f"Added {added_count} files")

    def select_folders(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.statusBar().showMessage(f"Scanning folder: {folder}")

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
                    normalized_path = self._normalize_path(file)
                    if normalized_path not in [self._normalize_path(f) for f in self.selected_files]:
                        try:
                            self.total_size += os.path.getsize(file)
                        except:
                            pass
                        self.selected_files.append(file)
                        self.file_list.addItem(file)
                        added_count += 1

                self._update_file_stats()
                self.statusBar().showMessage(
                    f"Added {added_count} files from folder")
            finally:
                progress.close()

    def clear_selected_files(self):
        self.selected_files.clear()
        self.file_list.clear()
        self.total_size = 0
        self._update_file_stats()
        self.statusBar().showMessage("Cleared file list")

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
                row = self.file_list.row(item)
                self.file_list.takeItem(row)

        self._update_file_stats()
        self.statusBar().showMessage(f"Removed {len(selected_items)} items")

    def save_logs(self):
        # Collect validation errors
        validation_errors = []

        if not self.media_id_edit.text():
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
        media_id = self.media_id_edit.text()

        transfer_type_name = self.transfer_type_combo.currentText()
        transfer_type = self.transfer_types.get(transfer_type_name, "")

        # Create log directory
        log_dir = os.path.join(self.log_folder_edit.text(),
                               datetime.datetime.now().strftime("%Y"))
        os.makedirs(log_dir, exist_ok=True)

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
                lambda hashes: self.start_file_processing(transfer_log, hashes, log_dir) 
                if hashes else None
            )
            self.hash_worker.start()
        else:
            # Skip checksums and proceed directly to file processing
            self.start_file_processing(transfer_log, {}, log_dir)

    def start_file_processing(self, transfer_log, hashes, log_dir):
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
            transfer_log, self.selected_files, hashes, log_dir)
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
            self.statusBar().showMessage("Log generation cancelled by user")
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
            self.statusBar().showMessage(
                f"Logs generated successfully - {len(self.selected_files)} files processed")

            # Open log files if requested
            if self.open_file_list_log_check.isChecked():
                self.open_file(file_path)

            if self.open_transfer_log_check.isChecked():
                year = datetime.datetime.now().strftime("%Y")
                yearly_log = os.path.join(os.path.dirname(
                    file_path), f"TransferLog_{year}.log")
                self.open_file(yearly_log)
        else:
            QMessageBox.critical(self, "Error", "Failed to save log file")
            self.statusBar().showMessage("Error: Failed to save log file")

    def cancel_hash_operation(self):
        """Cancel the hash calculation operation and entire logging process"""
        if hasattr(self, 'hash_worker'):
            self.hash_worker.cancel()
            self.statusBar().showMessage("Log generation canceled by user")
            
        # Close the progress dialog if it's open
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()

    def cancel_file_processing(self):
        """Cancel the file processing operation"""
        if hasattr(self, 'file_worker'):
            self.file_worker.cancel()
            self.statusBar().showMessage("File processing canceled by user")
            
        # Close the progress dialog if it's open
        if hasattr(self, 'file_progress_dialog'):
            self.file_progress_dialog.close()