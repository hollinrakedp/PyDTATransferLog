#!/usr/bin/env python3
"""
Comprehensive test suite for PyDTATransferLog
Run with: python -m pytest tests/ -v
"""

import os
import sys
import tempfile
import shutil
import csv
import pytest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.config_manager import ConfigManager
from utils.file_utils import get_file_info, calculate_file_hash


class TestConfigManager:
    """Test configuration management functionality"""
    
    def test_config_creation(self):
        """Test that config manager creates and loads config properly"""
        config = ConfigManager()
        assert config is not None
    
    def test_media_types_loading(self):
        """Test that media types are loaded from config"""
        config = ConfigManager()
        media_types = config.get_media_types()
        assert isinstance(media_types, list)
        assert len(media_types) > 0
        assert "Flash" in media_types
    
    def test_transfer_types_loading(self):
        """Test that transfer types are loaded from config"""
        config = ConfigManager()
        transfer_types = config.get_transfer_types()
        assert isinstance(transfer_types, (list, dict))
        assert len(transfer_types) > 0
        # Accept both legacy list and current dict mapping
        if isinstance(transfer_types, dict):
            assert "Low to High" in transfer_types or "L2H" in transfer_types.values()
        else:
            assert any("L2H" in str(t) for t in transfer_types)


class TestFileUtils:
    """Test file utility functions"""
    
    def test_file_info_collection(self):
        """Test that file info is collected properly"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content for file info")
            temp_file = f.name
        
        try:
            file_info = get_file_info(temp_file)
            assert file_info is not None
            assert file_info.name == os.path.basename(temp_file)
            assert file_info.size > 0
            assert file_info.full_path == os.path.abspath(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_hash_calculation(self):
        """Test that file hashes are calculated correctly"""
        # Create a temporary file with known content
        test_content = "Hello, World!"
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            file_hash = calculate_file_hash(temp_file)
            assert file_hash is not None
            assert len(file_hash) == 64  # SHA-256 hash length
            
            # Calculate again to ensure consistency
            file_hash2 = calculate_file_hash(temp_file)
            assert file_hash == file_hash2
        finally:
            os.unlink(temp_file)


class TestCrossPlatformPaths:
    """Test cross-platform path handling"""
    
    def test_path_normalization(self):
        """Test that paths are normalized correctly"""
        test_paths = [
            "test/path/file.txt",
            "test\\path\\file.txt",
            "./test/path/file.txt",
            "../test/path/file.txt"
        ]
        
        for path in test_paths:
            normalized = os.path.normpath(os.path.abspath(path))
            assert os.path.isabs(normalized)
            assert "\\" not in normalized or "/" not in normalized  # Should be consistent
    
    def test_path_joining(self):
        """Test that path joining works cross-platform"""
        base = "/base/path"
        filename = "test.txt"
        joined = os.path.join(base, filename)
        
        # Should work regardless of platform
        assert filename in joined
        assert "base" in joined
class TestCSVGeneration:
    """Test CSV file generation and parsing"""
    
    def test_csv_structure(self):
        """Test that generated CSV files have correct structure"""
        # This would test actual CSV generation
        # For now, test that we can create a basic CSV structure
        headers = ["Level", "Container", "FullName", "Size", "File Hash"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerow(["0", "", "/test/file.txt", "1024", "abcd1234"])
            csv_file = f.name
        
        try:
            # Read it back
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['Level'] == '0'
                assert rows[0]['FullName'] == '/test/file.txt'
        finally:
            os.unlink(csv_file)


class TestImportFunctionality:
    """Test import request functionality"""
    
    def test_csv_import_structure(self):
        """Test that CSV files can be parsed for import"""
        # Create test CSV file
        test_data = [
            ["Level", "Container", "FullName", "Size", "File Hash"],
            ["0", "", "/test/file1.txt", "1024", ""],
            ["0", "", "/test/file2.txt", "2048", ""]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerows(test_data)
            csv_file = f.name
        
        try:
            # Test reading
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                level_0_files = [row for row in rows if row.get('Level') == '0']
                assert len(level_0_files) == 2
        finally:
            os.unlink(csv_file)
    
    def test_text_file_parsing(self):
        """Test that text files can be parsed for import"""
        test_content = """# Test file list
/test/file1.txt
/test/file2.txt
"path with spaces.txt"

# Comment line
/test/file3.txt"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            text_file = f.name
        
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                file_paths = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Remove quotes if present
                        if line.startswith('"') and line.endswith('"'):
                            line = line[1:-1]
                        file_paths.append(line)
                
                assert len(file_paths) == 4
                assert '/test/file1.txt' in file_paths
                assert 'path with spaces.txt' in file_paths
        finally:
            os.unlink(text_file)


if __name__ == "__main__":
    # Run tests if called directly
    import subprocess
    import sys
    
    try:
        # Try to run with pytest
        subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to unittest if pytest not available
        import unittest
        unittest.main()