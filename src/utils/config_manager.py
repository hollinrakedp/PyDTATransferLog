import os
import configparser

class ConfigManager:
    """Class for managing application configuration"""
    
    DEFAULT_CONFIG = {
        "Paths": {
            "LogOutputFolder": "./logs",
        },
        "MediaTypes": {
            "Options": "HDD,SSD,USB Drive,DVD,CD,Network Share,Cloud Storage,FTP,Email,Other"
        },
        "NetworkList": {
            "Options": "NETWORK1,NETWORK2,NETWORK3,NETWORK4"
        },
        "TransferTypes": {
            "Options": "Archive:ARC,Export:EXP,Import:IMP,Transfer:XFR"
        }
    }
    
    def __init__(self, config_path):
        """Initialize the config manager"""
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        # Load config or create if doesn't exist
        if os.path.exists(config_path):
            self.config.read(config_path)
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default configuration file"""
        for section, options in self.DEFAULT_CONFIG.items():
            if section not in self.config:
                self.config.add_section(section)
            
            for option, value in options.items():
                self.config.set(section, option, value)
        
        self.save()
    
    def get(self, section, option, fallback=None):
        """Get a configuration value"""
        return self.config.get(section, option, fallback=fallback)
    
    def set(self, section, option, value):
        """Set a configuration value"""
        if section not in self.config:
            self.config.add_section(section)
        
        self.config.set(section, option, value)
    
    def get_list(self, section, option):
        """Get a list of items from a specified section and option"""
        items = self.get(section, option, fallback="")
        return [item.strip() for item in items.split(",") if item.strip()]
    
    def get_transfer_types(self):
        """Get transfer types mapping from the UI section"""
        items = self.get("UI", "TransferTypes", fallback="")
        mapping = {}
        for pair in items.split(","):
            if ":" in pair:
                name, abbr = pair.split(":", 1)
                mapping[name.strip()] = abbr.strip()
        return mapping
    
    def save(self):
        """Save configuration to file"""
        with open(self.config_path, "w") as f:
            self.config.write(f)