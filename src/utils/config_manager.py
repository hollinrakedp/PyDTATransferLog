import os
import configparser

class CommentedConfigParser(configparser.ConfigParser):
    """ConfigParser that preserves comments"""
    
    def __init__(self):
        super().__init__()
        self.comments = {
            "UI": {
                "_section": "; UI section contains user interface settings",
                "MediaTypes": "; Specifies the list of available media types that can be selected in the application.\n; These are the types of storage media used for file transfers.",
                "TransferTypes": "; Specifies the available transfer types and their abbreviations.\n; Format: <Full Name>:<Abbreviation>\n; Example: \"Low to High\" is abbreviated as \"L2H\".",
                "NetworkList": "; Specifies the list of available networks for the source and destination.\n; These represent the networks involved in the file transfer.\n; Example: IS001, System 99",
                "LocalNetwork": "; Specifies your local network/system name. Used to determine transfer direction (Incoming/Outgoing).\n; This should match one of the options in the NetworkList.",
                "MediaID": "; Specifies the list of available Media IDs that will be pre-populated for the user.\n; These may often be called a Control Number.",
                "Theme": "; Sets the theme to use for the application interface.\n; Leave blank to use the default theme.\n; Available themes: kaleidoscope"
            },
            "Logging": {
                "_section": "; Logging section contains settings for log file generation",
                "OutputFolder": "; Specifies the default folder where log files will be saved.\n; This path can be customized to store logs in a specific directory.\n; You can use a relative path (e.g., ./logs) or an absolute path (e.g., C:\\logs).\n; Ensure that the specified folder exists before running the application.",
                "TransferLogName": "; Specify the Transfer log name\n; Available tokens:\n; {date} - Current date\n; {date:format} - Current date (format can be yyyyMMdd, yyyy-MM-dd, etc.)\n; {time} - Current time\n; {time:format} - Current time (format can be HHmmss, HH-mm-ss, etc.)\n; {timestamp} - Timestamp in format yyyyMMdd-HHmmss\n; {username} - Current username\n; {computername} - Computer name\n; {transfertype} - Transfer type abbreviation (L2H, H2H, etc.)\n; {source} - Source network/system\n; {destination} - Destination network/system\n; {direction} - Transfer direction (Incoming/Outgoing) based on LocalNetwork setting\n; {mediatype} - Type of media (Flash, HDD, etc.)\n; {mediaid} - Media identifier\n; {counter} - Sequential number\n; {year} - Current year",
                "FileListName": "; Format for the file list CSV filename",
                "DateFormat": "; Date format for the {date} token if used",
                "TimeFormat": "; Time format for the {time} token if used",
                "FileDelimiter": "; - Delimiter: The character used to separate parts of the log file name.",
                "TransferLogPrefix": "; The base name for the transfer log file.",
                "FileListPrefix": "; The base name for the file list log file."
            }
        }
    
    def write(self, fp):
        """Write the configuration with comments"""
        for section in self.sections():
            fp.write(f"[{section}]\n")
            if section in self.comments and "_section" in self.comments[section]:
                fp.write(f"{self.comments[section]['_section']}\n")
            
            for key, value in self[section].items():
                if section in self.comments and key in self.comments[section]:
                    fp.write(f"{self.comments[section][key]}\n")
                fp.write(f"{key} = {value}\n")
            fp.write("\n")

class ConfigManager:
    """Class for managing application configuration"""

    DEFAULT_CONFIG = {
        "UI": {
            "MediaTypes": "Apricorn, Blu-ray, CD, DVD, Flash, HDD, microSD, SD, SSD",
            "TransferTypes": "Low to High:L2H, High to High:H2H, High to Low:H2L",
            "NetworkList": "Intranet, Customer, IS001, System 99",
            "MediaID": "",
            "Theme": "arc"
        },
        "Logging": {
            "OutputFolder": "./logs",
            "FileDelimiter": "_",
            "TransferLogPrefix": "DTATransferLog",
            "FileListPrefix": "DTAFileList"
        }
    }
    
    def __init__(self, config_path):
        """Initialize the config manager"""
        self.config_path = config_path
        self.config = CommentedConfigParser()
        
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
    
    def reload(self):
        """Reload configuration from file"""
        try:
            if os.path.exists(self.config_path):
                self.config = CommentedConfigParser()
                self.config.read(self.config_path)
                return True
            return False
        except Exception as e:
            print(f"Error reloading configuration: {str(e)}")
            return False