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
MediaTypes = Apricorn, Blu-ray, CD, DVD, Flash, HDD, microSD, SD, SSD
TransferTypes = Low to High:L2H, High to High:H2H, High to Low:H2L
NetworkList = Intranet, Customer, IS001, System 99
LocalNetwork = Intranet
MediaID = CN-123-
```

- **Theme**: Controls the application's visual theme (e.g., kaleidoscope). Leave blank to use the default theme.
- **MediaTypes**: Comma-separated list of media types available in the dropdown. These represent the physical or virtual storage media used for file transfers.
- **TransferTypes**: Comma-separated list of transfer types with their abbreviations (Type:Abbreviation). Examples include:
  - "Low to High:L2H" - For transfers from lower to higher security systems
  - "High to High:H2H" - For transfers between systems of equal high security
  - "High to Low:H2L" - For transfers from higher to lower security systems
- **NetworkList**: Available networks or systems for source and destination fields. These should represent all the networks or systems between which transfers might occur.
- **LocalNetwork**: Your local network name (helps determine transfer direction automatically). This should match one of the entries in NetworkList and will be used to determine if transfers are Incoming or Outgoing.
- **MediaID**: Prefixes for media identifiers or control numbers. These will be pre-populated in the Media ID field, allowing users to simply add unique identifiers afterward.

#### Logging Section

The Logging section controls how and where logs are generated:

```ini
[Logging]
OutputFolder = ./logs
TransferLogName = TransferLog_{year}.log
FileListName = {date:yyyy-MM-dd}_{username}_{transfertype}_{source}-{destination}_FileList.csv
DateFormat = yyyyMMdd
TimeFormat = HHmmss
```

- **OutputFolder**: Directory where logs will be saved. You can use either:
  - Relative paths (e.g., `./logs` for a logs folder in the application directory)
  - Absolute paths (e.g., `C:\TransferLogs` or `/var/log/transfers`)
  - Ensure the specified path exists or has proper permissions for file creation
- **TransferLogName**: Template for main log file naming, which tracks all transfers in a single file.
- **FileListName**: Template for individual transfer log naming. Each file transfer operation generates a separate file with this naming pattern.
  - Default format produces filenames like: `2025-04-29_Darren_L2H_Intranet-Customer_FileList.csv`
  - You can combine any of the tokens listed below to create custom naming patterns
- **DateFormat**: Format for date tokens in filenames when using the simple {date} token
- **TimeFormat**: Format for time tokens in filenames when using the simple {time} token

### File Naming Tokens

The application supports the following tokens in log file names:

| Token | Description | Example |
|-------|-------------|---------|
| `{date}` | Current date in format specified by DateFormat | 20250429 |
| `{date:format}` | Custom format date | 2025-04-29 (with format yyyy-MM-dd) |
| `{time}` | Current time in format specified by TimeFormat | 153045 |
| `{time:format}` | Custom format time | 15:30:45 (with format HH:mm:ss) |
| `{timestamp}` | Date and time combined | 20250429-153045 |
| `{username}` | Current system user | Darren |
| `{computername}` | Computer name | WORKSTATION-01 |
| `{transfertype}` | Transfer type abbreviation | L2H |
| `{source}` | Source network/system | Intranet |
| `{destination}` | Destination network/system | Customer |
| `{direction}` | Transfer direction (based on LocalNetwork) | Incoming or Outgoing |
| `{mediatype}` | Type of media | Flash |
| `{mediaid}` | Media identifier | CN-123-456 |
| `{counter}` | Sequential number for multiple transfers | 001 |
| `{year}` | Current year | 2025 |

### Customizing Date and Time Formats

When using the extended date and time tokens (`{date:format}` and `{time:format}`), you can use the following format specifiers:

- For dates:
  - `yyyy`: Four-digit year (2025)
  - `yy`: Two-digit year (25)
  - `MM`: Two-digit month (04)
  - `MMM`: Three-letter month abbreviation (Apr)
  - `MMMM`: Full month name (April)
  - `dd`: Two-digit day (29)
  
- For times:
  - `HH`: Two-digit hour in 24-hour format (15)
  - `hh`: Two-digit hour in 12-hour format (03)
  - `mm`: Two-digit minutes (30)
  - `ss`: Two-digit seconds (45)
  - `tt`: AM/PM indicator (PM)

### Example Configuration

Here's a complete example configuration with explanations:

```ini
[UI]
Theme = kaleidoscope
MediaTypes = Apricorn, Blu-ray, CD, DVD, Flash, HDD, microSD, SD, SSD, Network
TransferTypes = Low to High:L2H, High to High:H2H, High to Low:H2L, Lateral:LAT
NetworkList = Intranet, Customer, IS001, System 99, Vendor, Cloud
LocalNetwork = Intranet
MediaID = CN-123-

[Logging]
OutputFolder = C:\TransferLogs
TransferLogName = TransferLog_{year}.log
FileListName = {date:yyyy-MM-dd}_{username}_{transfertype}_{source}-{destination}_CN{mediaid}.csv
DateFormat = yyyyMMdd
TimeFormat = HHmmss
```

This configuration would create:
- A main log file named `TransferLog_2025.log` in the C:\TransferLogs directory
- Individual transfer logs like `2025-04-29_Steve_L2H_Intranet-Customer_CN456.csv` for each transfer operation

### Applying Configuration Changes

Changes to the `config.ini` file will take effect the next time you start the application. If the file is missing or corrupted, the application will create a new one with default values.

For organizations deploying PyDTATransferLog to multiple systems, consider:
1. Creating a standardized `config.ini` file with your organization's requirements
2. Distributing this file with your application deployment
3. Setting appropriate file permissions to prevent unauthorized modifications

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
