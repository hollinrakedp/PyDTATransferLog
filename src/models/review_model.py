import csv
import datetime
import os

from PySide6.QtCore import QDate


class ReviewModel:
    """Model for reviewing transfer logs"""

    def __init__(self, config):
        self.config = config

    def load_log_data(self, log_dir: str) -> list[list[str]]:
        """Load all log files from the log directory"""
        all_log_entries = []

        if not os.path.exists(log_dir):
            return []

        # Find all log files in the directory
        log_files = []
        try:
            for file in os.listdir(log_dir):
                if file.endswith('.log'):
                    log_files.append(os.path.join(log_dir, file))
        except OSError:
            return []

        if not log_files:
            return []

        # Process all log files and collect entries
        for log_file in log_files:
            try:
                with open(log_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    try:
                        next(reader)  # Skip header row
                    except StopIteration:
                        continue # Empty file
                    all_log_entries.extend(list(reader))
            except Exception:
                # Skip bad files
                continue

        return all_log_entries

    def load_file_details(self, file_list_path: str) -> tuple[list[str], list[list[str]]]:
        """Load details from a specific file list CSV"""
        if not os.path.exists(file_list_path):
            raise FileNotFoundError(f"File list {file_list_path} not found")

        with open(file_list_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return [], [] # Empty file
            rows = list(reader)
            return headers, rows

    def filter_entries(self, entries: list[list[str]],
                       start_date: QDate | None = None,
                       end_date: QDate | None = None,
                       field_index: int | None = None,
                       filter_value: str | None = None,
                       search_text: str | None = None) -> list[list[str]]:
        """Apply filters to log entries"""
        filtered = entries

        # Apply date range filter
        if start_date and end_date:
            # Transfer dates are typically in column 1 (index 1) in format MM/DD/YYYY
            filtered = [
                e for e in filtered if len(e) > 1 and self._is_date_in_range(e[1], start_date, end_date)
            ]

        # Apply field/value filter
        if field_index is not None and filter_value:
            filtered = [
                e for e in filtered if len(e) > field_index and filter_value in e[field_index]]

        # Apply search filter
        if search_text:
            text = search_text.lower()
            filtered = [e for e in filtered if any(
                text in field.lower() for field in e)]

        return filtered

    def _is_date_in_range(self, date_str: str, start_date: QDate, end_date: QDate) -> bool:
        """Check if a date string is within the specified range"""
        try:
            # Convert MM/DD/YYYY to a date object for comparison
            parts = date_str.split('/')
            if len(parts) != 3:
                return False

            month, day, year = map(int, parts)
            date = QDate(year, month, day)

            return date >= start_date and date <= end_date
        except (ValueError, TypeError):
            return False

    def get_unique_values(self, entries: list[list[str]], field_index: int) -> list[str]:
        """Get unique values for a specific field"""
        unique_values = set()
        for entry in entries:
            if len(entry) > field_index:
                value = entry[field_index]
                if value:  # Skip empty values
                    unique_values.add(value)
        return sorted(unique_values)

    def sort_entries(self, entries: list[list[str]], column: int, reverse: bool = False) -> None:
        """Sort entries in place based on column and order"""

        def sort_key(entry):
            if len(entry) <= column:
                return ""

            val = entry[column]

            # Handle specific columns
            if column == 1:  # Transfer Date (MM/DD/YYYY)
                try:
                    parts = val.split('/')
                    if len(parts) == 3:
                        return datetime.date(int(parts[2]), int(parts[0]), int(parts[1]))
                except (ValueError, IndexError):
                    pass
            elif column in [10, 11]:  # File Count, Total Size
                try:
                    return int(val)
                except ValueError:
                    return 0

            # Default string comparison (case-insensitive)
            return val.lower()

        entries.sort(key=sort_key, reverse=reverse)

    def paginate_entries(self, entries: list[list[str]], page: int, page_size: int) -> list[list[str]]:
        """Get a slice of entries for the current page"""
        if page_size <= 0: # "All" or invalid
            return entries

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(entries))
        return entries[start_idx:end_idx]

    def calculate_total_pages(self, total_entries: int, page_size: int) -> int:
        """Calculate total pages"""
        if page_size <= 0:
            return 1
        return max(1, (total_entries + page_size - 1) // page_size)

    def export_data(self, file_path: str, headers: list[str], data: list[list[str]]) -> None:
        """Export data to CSV"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(data)
