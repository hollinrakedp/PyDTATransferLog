import os
import hashlib
import re
import datetime
import socket

def get_all_files(directory):
    """
    Recursively get all files in a directory
    
    Args:
        directory (str): Directory path to scan
    
    Returns:
        list: List of absolute file paths
    """
    files = []
    
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            files.append(os.path.join(root, filename))
            
    return files

def calculate_file_hash(filepath, algorithm='sha256', buffer_size=65536):
    """
    Calculate a file hash using the specified algorithm
    
    Args:
        filepath (str): Path to the file
        algorithm (str): Hash algorithm to use (default: sha256)
        buffer_size (int): Size of buffer for reading the file
    
    Returns:
        str: Hexadecimal hash digest
    """
    if algorithm.lower() == 'sha256':
        hash_obj = hashlib.sha256()
    elif algorithm.lower() == 'md5':
        hash_obj = hashlib.md5()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    with open(filepath, 'rb') as f:
        buffer = f.read(buffer_size)
        while len(buffer) > 0:
            hash_obj.update(buffer)
            buffer = f.read(buffer_size)
            
    return hash_obj.hexdigest()

def get_file_size_str(size_bytes):
    """
    Convert file size in bytes to a human-readable string
    
    Args:
        size_bytes (int): File size in bytes
    
    Returns:
        str: Human-readable file size
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024*1024:
        return f"{size_bytes/1024:.2f} KB"
    elif size_bytes < 1024*1024*1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    else:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"

def is_valid_file(filepath):
    """
    Check if a file exists and is accessible
    
    Args:
        filepath (str): Path to the file
    
    Returns:
        bool: True if the file exists and is accessible, False otherwise
    """
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)

def format_filename(template, data=None, config=None, counter=1):
    """
    Format a filename template by replacing tokens with their values.
    
    Args:
        template: The filename template with tokens like {date}, {username}, etc.
        data: Dictionary with additional data values
        config: Config object for accessing configuration values
        counter: Counter value for the {counter} token
        
    Returns:
        The formatted filename with all tokens replaced
    """
    if not data:
        data = {}
    
    # Base replacements (always available)
    now = datetime.datetime.now()
    replacements = {
        'username': os.getlogin(),
        'computername': socket.gethostname(),
        'counter': str(counter).zfill(3),
        'year': now.strftime("%Y"),
        'timestamp': now.strftime("%Y%m%d-%H%M%S")
    }
    
    # Date and time formats
    date_format = config.get("Logging", "DateFormat", fallback="yyyyMMdd") if config else "yyyyMMdd"
    time_format = config.get("Logging", "TimeFormat", fallback="HHmmss") if config else "HHmmss"
    
    # Convert Python date format from config format
    date_format = date_format.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")
    time_format = time_format.replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
    
    replacements['date'] = now.strftime(date_format)
    replacements['time'] = now.strftime(time_format)
    
    # Add any additional data
    replacements.update(data)
    
    def replace_token(match):
        token = match.group(1)
        if ':' in token:
            # Handle formatted tokens like {date:yyyy-MM-dd}
            name, fmt = token.split(':', 1)
            if name == 'date':
                fmt = fmt.replace("yyyy", "%Y").replace("MM", "%m").replace("dd", "%d")
                return now.strftime(fmt)
            elif name == 'time':
                fmt = fmt.replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
                return now.strftime(fmt)
            else:
                return replacements.get(name, match.group(0))
        else:
            return replacements.get(token, match.group(0))
    
    # Replace tokens in the template
    result = re.sub(r'\{([^}]+)\}', replace_token, template)
    
    # Make sure the filename is valid
    result = sanitize_filename(result)
    
    return result


def sanitize_filename(filename):
    """
    Sanitize a filename to ensure it's valid on the current platform
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Ensure filename isn't too long
    max_length = 240  # Windows MAX_PATH is 260, leave room for path
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length-len(ext)] + ext
        
    return filename