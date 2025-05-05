import os
import sys
import shutil
import configparser

class ConfigManager:
    """Class for managing application configuration"""

    def __init__(self, config_filename="config.ini"):
        """Initialize the config manager"""
        # Determine the base path based on whether we're running in PyInstaller or not
        if hasattr(sys, '_MEIPASS'):
            self.base_path = sys._MEIPASS  # Temporary directory for PyInstaller
        else:
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Parent of utils directory
        
        # User config is always in the current working directory for consistency
        self.config_path = os.path.join(os.getcwd(), config_filename)
        
        # Path to the bundled config
        self.bundled_config_path = os.path.join(self.base_path, config_filename)
        
        # Initialize standard ConfigParser
        self.config = configparser.ConfigParser()
        
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_path):
            self._create_default_config()
        
        # Load configuration
        self.config.read(self.config_path)        
        # Cache for transfer types mapping
        self._transfer_types_cache = None
    
    def _create_default_config(self):
        """Create a default configuration file by copying the bundled config"""
        try:
            # Ensure bundled config exists
            if not os.path.exists(self.bundled_config_path):
                raise FileNotFoundError(f"Bundled configuration file not found at: {self.bundled_config_path}")
                
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Copy the bundled config
            shutil.copy(self.bundled_config_path, self.config_path)
            print(f"Created default configuration at: {self.config_path}")
            
        except Exception as e:
            print(f"ERROR: Failed to create default configuration: {str(e)}")
            print("The application may not function correctly without a valid configuration file.")
    
    def get(self, section, option, fallback=None):
        """Get a configuration value"""
        return self.config.get(section, option, fallback=fallback)
    
    def set(self, section, option, value):
        """Set a configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
    
    def get_list(self, section, option):
        """Get a list of items from a specified section and option"""
        items = self.get(section, option, fallback="")
        return [item.strip() for item in items.split(",") if item.strip()]
    
    def get_transfer_types(self):
        """Get transfer types mapping from the UI section"""
        # Use cached value if available
        if self._transfer_types_cache is not None:
            return self._transfer_types_cache
            
        items = self.get("UI", "TransferTypes", fallback="")
        mapping = {}
        for pair in items.split(","):
            if ":" in pair:
                name, abbr = pair.split(":", 1)
                mapping[name.strip()] = abbr.strip()

        # Cache the result
        self._transfer_types_cache = mapping
        return mapping
    
    def save(self):
        """Save configuration to file"""
        with open(self.config_path, "w") as f:
            self.config.write(f)
    
    def reload(self):
        """Reload configuration from file"""
        try:
            if os.path.exists(self.config_path):
                self.config = configparser.ConfigParser()
                self.config.read(self.config_path)
                self._transfer_types_cache = None
                return True
            return False
        except Exception as e:
            print(f"Error reloading configuration: {str(e)}")
            return False