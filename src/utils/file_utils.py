import os
import hashlib

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