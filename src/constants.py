"""Constants used throughout the application"""

# Transfer Log CSV headers
TRANSFER_LOG_HEADERS = [
    "Timestamp", "Transfer Date", "Username", "Computer Name",
    "Media Type", "Media ID", "Transfer Type", "Source",
    "Destination", "File Count", "Total Size", "File Log"
]

# File List CSV headers
FILE_LIST_HEADERS = [
    "Level", "Container", "FullName", "Size", "File Hash"
]

# UI display versions of headers (can be slightly different if needed)
TRANSFER_LOG_DISPLAY_HEADERS = [
    "Timestamp", "Transfer Date", "Username", "ComputerName", "MediaType",
    "MediaID", "TransferType", "Source", "Destination", "File Count", "Total Size", "File Log"
]

FILE_LIST_DISPLAY_HEADERS = [
    "", "Folder", "Filename", "Size", "File Hash"
]