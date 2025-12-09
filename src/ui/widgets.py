"""Shared UI widgets for the PyDTATransferLog application"""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QPainter, QPen
from PySide6.QtWidgets import QListWidget

from utils.file_utils import get_all_files


class DragDropFileListWidget(QListWidget):
    """Reusable file list widget with drag and drop support.

    The parent widget must implement:
    - _add_file(file_path: str) -> bool: Add a file to the list, return True if added
    - _update_file_stats(): Update file statistics display
    - app.set_status_message(message: str): Update status bar message
    """

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

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Accept the drag movement if it contains file URLs or text"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Process dropped files and folders"""
        mime_data = event.mimeData()

        # Process URLs (files and folders)
        if mime_data.hasUrls():
            self._process_dropped_urls(mime_data.urls())
        # Process text (might be file paths)
        elif mime_data.hasText():
            self._process_dropped_text(mime_data.text())

        event.acceptProposedAction()

    def _process_dropped_urls(self, urls):
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

    def _process_dropped_text(self, text):
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
                self.main_window.app.set_status_message(f"Error scanning folder: {e!s}")

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
            icon_text = "📁➕"  # ruff: noqa: RUF001 - intentional UI glyph
            text = "Drag and drop files or folders here"

            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                f"{icon_text}\n\n{text}"
            )

            painter.restore()
