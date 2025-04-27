import os
import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QComboBox, QSplitter, QTreeWidget, 
                              QTreeWidgetItem, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon
from utils.config_manager import ConfigManager
from models.log_model import TransferLog, FileInfo

class TransferLogReviewerWindow(QMainWindow):
    def __init__(self, year=None):
        super().__init__()
        self.setWindowTitle("DTA Transfer Log Reviewer")
        
        # Set up icon
        icon_path = os.path.join("resources", "icons", "dtatransferlog.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        # Load configuration
        self.config = ConfigManager("config.ini")
        self.log_dir = self.config.get("Paths", "LogOutputFolder", fallback="./logs")
        
        # Set initial year
        self.selected_year = year or datetime.datetime.now().strftime("%Y")
        
        # Set up the UI
        self._setup_ui()
        
        # Load available years
        self.load_available_years()
        
        # Set the year if provided
        if year:
            index = self.year_combo.findText(year)
            if index >= 0:
                self.year_combo.setCurrentIndex(index)
        
        # Load log file
        self.load_log_file()
        
    def _setup_ui(self):
        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Year selection
        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Select Year:"))
        self.year_combo = QComboBox()
        self.year_combo.currentTextChanged.connect(self.year_changed)
        year_layout.addWidget(self.year_combo)
        year_layout.addStretch()
        main_layout.addLayout(year_layout)
        
        # Splitter to replace PanedWindow
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # Upper pane - log content
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        self.log_tree = QTreeWidget()
        self.log_tree.setHeaderLabels([
            "Timestamp", "Transfer Date", "Username", "ComputerName", "MediaType",
            "MediaID", "TransferType", "Source", "Destination", "File Count", "Total Size", "File Log"
        ])
        self.log_tree.currentItemChanged.connect(self.display_transfer_details)
        self.log_tree.setAlternatingRowColors(True)
        self.log_tree.setSortingEnabled(True)
        
        log_layout.addWidget(self.log_tree)
        splitter.addWidget(log_widget)
        
        # Lower pane - transfer details
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        
        self.details_tree = QTreeWidget()
        self.details_tree.setHeaderLabels([
            "Level", "Container", "Full Name", "Size", "SHA-256"
        ])
        self.details_tree.setAlternatingRowColors(True)
        
        details_layout.addWidget(self.details_tree)
        splitter.addWidget(details_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 300])
        
        # Set reasonable initial size for the window
        self.resize(1000, 700)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def load_available_years(self):
        """Load available log years from the log directory"""
        self.year_combo.clear()
        
        years = []
        if os.path.exists(self.log_dir):
            for item in os.listdir(self.log_dir):
                if os.path.isdir(os.path.join(self.log_dir, item)) and item.isdigit():
                    years.append(item)
        
        # If no years found, add current year
        if not years:
            years.append(datetime.datetime.now().strftime("%Y"))
        
        # Sort years in descending order
        years.sort(reverse=True)
        self.year_combo.addItems(years)
        
        # Set to selected year if available, otherwise first year in list
        index = self.year_combo.findText(self.selected_year)
        if index >= 0:
            self.year_combo.setCurrentIndex(index)
        elif self.year_combo.count() > 0:
            self.year_combo.setCurrentIndex(0)
    
    def year_changed(self, year):
        """Called when year selection changes"""
        self.selected_year = year
        self.load_log_file()
    
    def load_log_file(self):
        """Load the transfer log file for the selected year"""
        self.log_tree.clear()
        self.details_tree.clear()
        
        year_dir = os.path.join(self.log_dir, self.selected_year)
        
        if not os.path.exists(year_dir):
            self.statusBar().showMessage(f"No logs found for year {self.selected_year}")
            return
            
        log_files = []
        for file in os.listdir(year_dir):
            if file.endswith(".txt") and not file.endswith("_files.txt"):
                log_files.append(os.path.join(year_dir, file))
                
        if not log_files:
            self.statusBar().showMessage(f"No logs found for year {self.selected_year}")
            return
            
        # Load each log file
        for log_file in log_files:
            try:
                log = TransferLog.load_from_file(log_file)
                self._add_log_to_tree(log, log_file)
            except Exception as e:
                print(f"Error loading log {log_file}: {str(e)}")
                
        self.log_tree.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self.statusBar().showMessage(f"Loaded {len(log_files)} logs for {self.selected_year}")
                
    def _add_log_to_tree(self, log, log_file):
        """Add a log entry to the tree view"""
        item = QTreeWidgetItem([
            log.timestamp,
            log.transfer_date,
            log.username,
            log.computer_name,
            log.media_type,
            log.media_id,
            log.transfer_type,
            log.source,
            log.destination,
            str(log.file_count),
            str(log.total_size),
            os.path.basename(log_file)
        ])
        
        # Store the log_file path as item data
        item.setData(0, Qt.ItemDataRole.UserRole, log_file)
        
        self.log_tree.addTopLevelItem(item)
    
    def display_transfer_details(self, current, previous):
        """Display file details for the selected transfer log"""
        if not current:
            return
            
        self.details_tree.clear()
        
        # Get the log file path from the item data
        log_file = current.data(0, Qt.ItemDataRole.UserRole)
        if not log_file:
            return
            
        # Get corresponding file list log
        file_list_log = log_file.replace(".txt", "_files.txt")
        if not os.path.exists(file_list_log):
            return
            
        # Load file list
        try:
            with open(file_list_log, "r", encoding="utf-8") as f:
                lines = f.readlines()
                
            containers = {}
            
            for line in lines:
                if line.startswith("#") or not line.strip():
                    continue
                    
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    level = parts[0]
                    container = parts[1]
                    full_path = parts[2]
                    
                    size = ""
                    sha256 = ""
                    
                    if len(parts) >= 4:
                        size = parts[3]
                    if len(parts) >= 5:
                        sha256 = parts[4]
                        
                    # Create container item if it doesn't exist
                    if container not in containers:
                        container_item = QTreeWidgetItem([level, container, "", "", ""])
                        self.details_tree.addTopLevelItem(container_item)
                        containers[container] = container_item
                        
                    # Add file item to container
                    file_item = QTreeWidgetItem([level, "", full_path, size, sha256])
                    containers[container].addChild(file_item)
                    
            # Expand all containers
            self.details_tree.expandAll()
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading file list: {str(e)}")