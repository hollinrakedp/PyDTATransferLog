# PyDTATransferLog

A cross-platform utility for logging file transfers between systems.

## Features

- **Comprehensive Transfer Logging**: Create detailed logs of file transfers including user information, timestamps, source and destination systems, and transfer direction.
- **Media Tracking**: Categorize transfers by media type (Flash Drive, HDD, SSD, etc.) and assign custom media IDs for better organization.
- **Archive Inspection**: Automatically extract and log file listings from common archive formats:
  - ZIP archives (.zip)
  - TAR archives (.tar)
  - Gzipped archives (.gz, .tgz)
  - And other compressed formats
- **Detailed File Metadata**: Capture file size, modification dates, and permission information for each transferred file.
- **File Verification**: Generate SHA-256 checksums for transferred files to ensure data integrity.
- **Archive Content Logging**: View and log the contents of archived files without extraction, providing visibility into packaged data.
- **Transfer History**: Built-in log viewer to review past transfers with filtering and search capabilities.
- **Flexible Interface**: User-friendly GUI with drag-and-drop support and an experimental command-line interface for automation.
- **Cross-Platform Compatibility**: Works on Windows and Linux operating systems.
- **Customizable Logging**: Configure log format, location, and naming conventions through a simple configuration file.

## Installation

### Download Pre-built Binaries

1. Go to the [Releases](https://github.com/your-org/PyDTATransferLog/releases) page of the PyDTATransferLog repository.
2. Download the appropriate binary for your operating system:
   - **Windows**: `PyDTATransferLog-win-x64.zip`
   - **Linux**: `PyDTATransferLog-linux-x64.tar.gz`

3. Extract the downloaded archive to your preferred location.

4. **Windows users**: 
   - Double-click the `PyDTATransferLog.exe` executable to run the application.

5. **Linux users**:
   - Make the executable file permissions executable: `chmod +x PyDTATransferLog`
   - Run the application: `./PyDTATransferLog`

### Install from Source

1. Ensure you have Python 3.10 or later installed on your system.
   - Verify with: `python --version` or `python3 --version`
   - Download from [python.org](https://www.python.org/downloads/) if needed.

2. Clone the repository:
   ```bash
   git clone https://github.com/your-org/PyDTATransferLog.git
   cd PyDTATransferLog
   ```

3. Create and activate a virtual environment (recommended):
   - **Windows**:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```
   - **Linux/macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python src/main.py
   ```

### First-Time Setup

1. After installation, the application will create a `config.ini` file in the `src` directory if it doesn't already exist.

2. Review the default configuration settings and modify them as needed:
   - Set the preferred output folder for logs
   - Configure media types and transfer types
   - Customize log file naming formats

3. The application will create a logs directory to store transfer logs if it doesn't exist.

## Usage

### GUI Mode

To use the PyDTATransferLog in GUI mode, follow these steps:

1. Launch the application:
   - **From Binary**: Double-click the PyDTATransferLog executable
   - **From Source**: Run `python src/main.py`

2. **Configure Transfer Details**:
   - **Media Type**: Select the type of media used for transfer (Flash Drive, HDD, etc.)
   - **Media ID**: Enter a unique identifier for the transfer media
   - **Source**: Select or enter the source system name
   - **Destination**: Select or enter the destination system name
   - **Transfer Type**: Choose between "Low to High" (L2H) or other configured transfer types

3. **Add Files and Folders**:
   - Click the **Add Files** button to select individual files for logging
   - Click the **Add Folders** button to select entire directories
   - **Drag and Drop** files or folders directly into the file list area
   - The application will automatically scan and display the selected items

4. **File Verification**:
   - Enable the **Generate SHA-256 Checksums** option to create checksums for all files
   - Checksums are stored in the log file for future verification

5. **Generate Transfer Log**:
   - Click the **Start Transfer** button to generate the log
   - The application will process all files and archives, collecting metadata
   - A log file will be created according to the naming pattern in config.ini
   - A confirmation dialog will appear when the log is complete

6. **Review Transfer Logs**:
   - Click the **Review** button to open the log viewer
   - Navigate through previous transfer logs
   - Search for specific transfers by date, user, or transfer type
   - View detailed file listings and checksums for each transfer

### CLI Mode (Experimental)

The command-line interface allows for scripted or automated logging of transfers. This mode is currently experimental and may not support all GUI features.

**Basic Usage**:

```bash
python src/main.py -c --media-type "Flash Drive" --media-id "USB123" --transfer-type "L2H" --source "System1" --destination "System2" --files file1.txt file2.txt --folders folder1 folder2
```

**Available Options**:

- `--media-type`: Type of transfer media (e.g., "Flash Drive", "HDD")
- `--media-id`: Unique identifier for the media
- `--transfer-type`: Type of transfer (e.g., "L2H" or "Low to High")
- `--source`: Source system name
- `--destination`: Destination system name
- `--files`: Space-separated list of files to include
- `--folders`: Space-separated list of folders to include
- `--sha256`: Enable SHA-256 checksum generation
- `--list-archives`: Enable listing of files within archives
- `--output-dir`: Specify an alternative output directory for logs
- `--help`: Display help information

**Example with Checksums**:

```bash
python src/main.py -c --media-type "HDD" --media-id "EXT-500GB" --transfer-type "L2H" --source "Workstation" --destination "Server" --files document.pdf image.jpg --folders /path/to/data --sha256 --list-archives
```


## Configuration

PyDTATransferLog is highly configurable through its `config.ini` file, typically located in the `src` directory. This file controls the application's behavior, appearance, and logging formats.

### Available Options

#### UI Section

The UI section controls the application's appearance and available options in the interface:

```ini
[UI]
Theme = Light
MediaTypes = Flash Drive, HDD, SSD, Network
TransferTypes = Low to High:L2H, High to Low:H2L
NetworkList = Intranet, Internet, Customer, Vendor
LocalNetwork = Intranet
```

- **Theme**: Controls the application's visual theme (Light, Dark)
- **MediaTypes**: Comma-separated list of media types available in the dropdown
- **TransferTypes**: Comma-separated list of transfer types with optional abbreviations (Type:Abbreviation)
- **NetworkList**: Available networks for source and destination fields
- **LocalNetwork**: Your local network name (helps determine transfer direction)

#### Logging Section

The Logging section controls how and where logs are generated:

```ini
[Logging]
OutputFolder = ./logs
TransferLogName = TransferLog_{year}.log
FileListName = {date}_{username}_{transfertype}_{source}-{destination}_{counter}.log
DateFormat = yyyyMMdd
TimeFormat = HHmmss
MaxFileScanDepth = 5
IncludeEmptyFolders = True
DefaultSHA256 = False
MaxFilesBeforeConfirm = 1000
```

- **OutputFolder**: Directory where logs will be saved (relative or absolute path)
- **TransferLogName**: Template for main log file naming
- **FileListName**: Template for individual transfer log naming
- **DateFormat**: Format for date tokens in filenames
- **TimeFormat**: Format for time tokens in filenames
- **MaxFileScanDepth**: Maximum folder depth to scan for files
- **IncludeEmptyFolders**: Whether to include empty folders in logs (True/False)
- **DefaultSHA256**: Default setting for SHA-256 checksum generation (True/False)
- **MaxFilesBeforeConfirm**: Show confirmation if transfer contains more than this number of files

### File Naming Tokens

The application supports the following tokens in log file names:

| Token | Description | Example |
|-------|-------------|---------|
| `{date}` | Current date | 20250428 |
| `{date:format}` | Custom format date | 2025-04-28 |
| `{time}` | Current time | 153045 |
| `{time:format}` | Custom format time | 15:30:45 |
| `{timestamp}` | Date and time | 20250428-153045 |
| `{username}` | Current user | Darren |
| `{computername}` | Computer name | WORKSTATION-01 |
| `{transfertype}` | Transfer type | L2H |
| `{source}` | Source system | Intranet |
| `{destination}` | Destination system | Customer |
| `{direction}` | Transfer direction | Outgoing |
| `{mediatype}` | Type of media | Flash Drive |
| `{mediaid}` | Media identifier | USB123 |
| `{counter}` | Sequential number | 001 |
| `{year}` | Current year | 2025 |

### Example Configuration

Here's a complete example configuration:

```ini
[UI]
Theme = Light
MediaTypes = Flash Drive, HDD, SSD, Network, CD/DVD, Tape
TransferTypes = Low to High:L2H, High to Low:H2L, Lateral:LAT
NetworkList = Intranet, Internet, Customer, Vendor, Partner, Cloud
LocalNetwork = Intranet

[Logging]
OutputFolder = ./logs
TransferLogName = TransferLog_{year}.log
FileListName = {date}_{username}_{transfertype}_{source}-{destination}_{counter}.log
DateFormat = yyyyMMdd
TimeFormat = HHmmss
MaxFileScanDepth = 5
IncludeEmptyFolders = True
DefaultSHA256 = False
MaxFilesBeforeConfirm = 1000
```

This configuration would create log files like:
- `TransferLog_2025.log` (Transfer Log)
- `20250428_Darren_L2H_Intranet-Customer_001.log` (File List Log)

## Development

### Prerequisites

To develop for PyDTATransferLog, you'll need:

- **Python 3.10+**: The application is built on Python 3.10 or higher
- **Git**: For version control
- **PyQt5/PySide6**: For the graphical user interface
- **IDE**: Visual Studio Code, PyCharm, or any Python IDE of your choice

### Setting Up the Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/PyDTATransferLog.git
   cd PyDTATransferLog
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up pre-commit hooks (optional):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Project Structure

- `src/`: Main source code directory
  - `main.py`: Application entry point
  - `config.ini`: Configuration file
  - `constants.py`: Application constants
  - `models/`: Data models
  - `ui/`: User interface code
  - `utils/`: Utility functions
  - `resources/`: Application resources (icons, styles)
- `tests/`: Unit and integration tests
- `logs/`: Default directory for generated logs
- `build/`: Build artifacts (created during build process)
- `dist/`: Distribution packages (created during build process)

### Running Tests

Run the test suite to ensure your changes don't break existing functionality:

```bash
python -m unittest discover tests
```

## Building the Application

### Prerequisites for Building

- **PyInstaller**: For creating standalone executables
- **UPX** (optional): For compressing executables
- **Sign tools** (optional): For signing Windows executables

### Building for Windows

1. Install PyInstaller if not already installed:
   ```bash
   pip install pyinstaller
   ```

2. Build using the included spec file:
   ```bash
   pyinstaller main.spec
   ```

3. The executable will be created in the `dist` folder.

4. For a more customized build:
   ```bash
   pyinstaller --name="PyDTATransferLog" --windowed --icon=src/resources/dtatransferlog.ico --add-data="src/resources;resources" src/main.py
   ```

### Building for Linux

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build using the spec file:
   ```bash
   pyinstaller main.spec
   ```

3. For a manual build:
   ```bash
   pyinstaller --name="PyDTATransferLog" --icon=src/resources/dtatransferlog.png --add-data="src/resources:resources" src/main.py
   ```

### Building for Different Platforms

The project uses GitHub Actions workflows to automate builds for multiple platforms. See the `.github/workflows/build.yaml` file for configuration details.

To manually build for all supported platforms, you'll need to:

1. Set up the appropriate environment for each target platform
2. Run the PyInstaller command with platform-specific options
3. Package the resulting binaries appropriately (.zip for Windows, .tar.gz for Linux)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
