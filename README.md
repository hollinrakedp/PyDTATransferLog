# PyDTATransferLog

A cross-platform utility for logging file transfers between systems.

## Features

- **File Transfer Request Generation**: Create detailed requests for file transfers with purpose justification and file inventories.
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
- **Flexible Interface**: User-friendly GUI with tabbed interface and command-line interface for automation.
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
   - Set the preferred output folder for transfer logs
   - Set the preferred output folder for file transfer requests
   - Configure media types and transfer types
   - Customize log and request file naming formats

3. The application will create logs and requests directories to store transfer logs and file transfer requests if they don't exist.

## Usage

### GUI Mode

To use the PyDTATransferLog in GUI mode, follow these steps:

1. Launch the application:
   - **From Binary**: Double-click the PyDTATransferLog executable
   - **From Source**: Run `python src/main.py`

The application opens with a tabbed interface containing three main sections:

#### Request Tab

The Request tab allows you to generate file transfer requests for approval:

1. **Configure Request Details**:
   - **Requestor**: Enter the name of the person making the request
   - **Purpose**: Provide justification or purpose for the file transfer request
   - **Request Date**: Set the date of the request (defaults to current date)
   - **Computer Name**: Computer name (defaults to current hostname)

2. **Add Files and Folders**:
   - Click the **Add Files** button to select individual files for the request
   - Click the **Add Folders** button to select entire directories
   - **Drag and Drop** files or folders directly into the file list area
   - The application will automatically scan and display the selected items

3. **File Verification**:
   - Enable the **Generate SHA-256 Checksums** option to create checksums for all files
   - Checksums are stored in the request file for verification purposes

4. **Generate Request**:
   - Click the **Create Request** button to generate the request file
   - The application will process all files, collecting metadata
   - A request file will be created according to the naming pattern in config.ini
   - A confirmation dialog will appear when the request is complete

#### Log Tab

The Log tab is used for logging actual file transfers:

1. **Configure Transfer Details**:
   - **Media Type**: Select the type of media used for transfer (Flash Drive, HDD, etc.)
   - **Media ID**: Enter a unique identifier for the transfer media
   - **Source**: Select or enter the source system name
   - **Destination**: Select or enter the destination system name
   - **Transfer Type**: Choose between "Low to High" (L2H) or other configured transfer types

2. **Add Files and Folders**:
   - Click the **Add Files** button to select individual files for logging
   - Click the **Add Folders** button to select entire directories
   - **Drag and Drop** files or folders directly into the file list area
   - The application will automatically scan and display the selected items

3. **File Verification**:
   - Enable the **Generate SHA-256 Checksums** option to create checksums for all files
   - Checksums are stored in the log file for future verification

4. **Generate Transfer Log**:
   - Click the **Start Transfer** button to generate the log
   - The application will process all files and archives, collecting metadata
   - A log file will be created according to the naming pattern in config.ini
   - A confirmation dialog will appear when the log is complete

#### Review Tab

The Review tab provides access to historical transfer logs:

1. **Review Transfer Logs**:
   - Navigate through previous transfer logs
   - Search for specific transfers by date, user, or transfer type
   - View detailed file listings and checksums for each transfer

### Starting with a Specific Tab

You can control which tab the application opens to in two ways:

#### Using Command Line Arguments

```bash
# Start with Request tab (default)
python src/main.py --tab request
# or
python src/main.py --tab 0

# Start with Log tab  
python src/main.py --tab log
# or
python src/main.py --tab 1

# Start with Review tab
python src/main.py --tab review
# or
python src/main.py --tab 2
```

#### Using Configuration File

Set the `DefaultTab` option in the `[UI]` section of `config.ini`:

```ini
[UI]
DefaultTab = Log    # Opens to Log tab by default
```

**Note**: Command line arguments take priority over the configuration file setting. If you specify `--tab` on the command line, it will override the `DefaultTab` configuration.

### CLI Mode

The command-line interface allows for scripted or automated processing. The CLI supports two modes: **Transfer Logging** and **File Transfer Requests**.

#### Transfer Logging CLI Mode

Use the transfer logging mode to record actual file transfers:

**Basic Usage**:

```bash
python src/main.py -t --media-type "Flash Drive" --media-id "USB123" --transfer-type "L2H" --source "System1" --destination "System2" --files file1.txt file2.txt --folders folder1 folder2
```

**Available Options**:

- `-t, --transfer`: Enable transfer logging CLI mode
- `--media-type`: Type of transfer media (e.g., "Flash Drive", "HDD")
- `--media-id`: Unique identifier for the media
- `--transfer-type`: Type of transfer (e.g., "L2H" or "Low to High")
- `--source`: Source system name
- `--destination`: Destination system name
- `--files`: Space-separated list of files to include
- `--folders`: Space-separated list of folders to include
- `--sha256`: Enable SHA-256 checksum generation
- `--output`: Specify an alternative output directory for logs
- `--help`: Display help information

**Example with Checksums**:

```bash
python src/main.py -t --media-type "HDD" --media-id "EXT-500GB" --transfer-type "L2H" --source "Workstation" --destination "Server" --files document.pdf image.jpg --folders /path/to/data --sha256
```

#### File Transfer Request CLI Mode

Use the request mode to generate file transfer requests for approval:

**Basic Usage**:

```bash
python src/main.py -r --requestor "John Doe" --purpose "Project documentation transfer" --files file1.txt file2.txt --folders folder1 folder2
```

**Available Options**:

- `-r, --request`: Enable file transfer request CLI mode
- `--requestor`: Name of the person making the request (required)
- `--purpose`: Purpose/justification for the request (required)
- `--request-date`: Request date (MM/dd/yyyy format, defaults to today)
- `--computer-name`: Computer name (defaults to current hostname)
- `--files`: Space-separated list of files to include
- `--folders`: Space-separated list of folders to include
- `--sha256`: Enable SHA-256 checksum generation
- `--output`: Specify an alternative output directory for requests
- `--help`: Display help information

**Example with Checksums**:

```bash
python src/main.py -r --requestor "Jane Smith" --purpose "Data analysis files for Q4 report" --request-date "12/15/2025" --files analysis.xlsx report.docx --folders /path/to/datasets --sha256
```

#### Version Information

```bash
python src/main.py -V
python src/main.py --version
```

#### CLI Help

Get help for specific CLI modes:

```bash
python src/main.py -t --help    # Transfer logging help
python src/main.py -r --help    # File request help
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
DefaultTab = 
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
- **DefaultTab**: Sets which tab the application opens to by default. Valid options are:
  - **Request**, **Log**, **Review** (case-insensitive) 
  - **0**, **1**, **2** (numeric equivalents)
  - Leave blank to default to the Request tab (0)

#### Requests Section

The Requests section controls how and where file transfer requests are generated:

```ini
[Requests]
OutputFolder = ./requests
EnableRequestLog = true
RequestLogName = RequestLog_{year}.log
FileListName = {date:yyyyMMdd}_{username}_Request_{counter}.csv
DateFormat = yyyyMMdd
TimeFormat = HHmmss
```

- **OutputFolder**: Directory where request files will be saved. You can use either:
  - Relative paths (e.g., `./requests` for a requests folder in the application directory)
  - Absolute paths (e.g., `C:\TransferRequests` or `/var/log/requests`)
  - Ensure the specified path exists or has proper permissions for file creation
- **EnableRequestLog**: Controls whether a summary log of all requests is created
  - Set to `true` to create a summary log of all requests (recommended)
  - Set to `false` to only create individual request file lists
- **RequestLogName**: Template for main request log file naming, which tracks all requests in a single file
  - Only used if EnableRequestLog is true
  - Default format produces filenames like: `RequestLog_2025.log`
- **FileListName**: Template for individual request file naming. Each request operation generates a separate file with this naming pattern
  - Default format produces filenames like: `20250429_JohnDoe_Request_001.csv`
  - You can combine any of the tokens listed below to create custom naming patterns
- **DateFormat**: Format for date tokens in filenames when using the simple {date} token
- **TimeFormat**: Format for time tokens in filenames when using the simple {time} token

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

The application supports the following tokens in log and request file names:

| Token | Description | Example | Available In |
|-------|-------------|---------|--------------|
| `{date}` | Current date in format specified by DateFormat | 20250429 | Logging, Requests |
| `{date:format}` | Custom format date | 2025-04-29 (with format yyyy-MM-dd) | Logging, Requests |
| `{time}` | Current time in format specified by TimeFormat | 153045 | Logging, Requests |
| `{time:format}` | Custom format time | 15:30:45 (with format HH:mm:ss) | Logging, Requests |
| `{timestamp}` | Date and time combined | 20250429-153045 | Logging, Requests |
| `{username}` | Current system user | Darren | Logging, Requests |
| `{computername}` | Computer name | WORKSTATION-01 | Logging, Requests |
| `{transfertype}` | Transfer type abbreviation | L2H | Logging only |
| `{source}` | Source network/system | Intranet | Logging only |
| `{destination}` | Destination network/system | Customer | Logging only |
| `{direction}` | Transfer direction (based on LocalNetwork) | Incoming or Outgoing | Logging only |
| `{mediatype}` | Type of media | Flash | Logging only |
| `{mediaid}` | Media identifier | CN-123-456 | Logging only |
| `{counter}` | Sequential number for multiple transfers/requests | 001 | Logging, Requests |
| `{year}` | Current year | 2025 | Logging, Requests |

**Note**: Request file naming uses a subset of these tokens since requests don't include transfer-specific details like media type, source/destination, or transfer direction.

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

[Requests]
OutputFolder = C:\TransferRequests
EnableRequestLog = true
RequestLogName = RequestLog_{year}.log
FileListName = {date:yyyyMMdd}_{username}_Request_{counter}.csv
DateFormat = yyyyMMdd
TimeFormat = HHmmss
```

This configuration would create:
- A main transfer log file named `TransferLog_2025.log` in the C:\TransferLogs directory
- Individual transfer logs like `2025-04-29_Steve_L2H_Intranet-Customer_CN456.csv` for each transfer operation
- A main request log file named `RequestLog_2025.log` in the C:\TransferRequests directory
- Individual request files like `20250429_JohnDoe_Request_001.csv` for each request

### Applying Configuration Changes

Changes to the `config.ini` file will take effect the next time you start the application. If the file is missing or corrupted, the application will create a new one with default values.

For organizations deploying PyDTATransferLog to multiple systems, consider:
1. Creating a standardized `config.ini` file with your organization's requirements
2. Distributing this file with your application deployment
3. Setting appropriate file permissions to prevent unauthorized modifications
4. Configuring appropriate output directories for both transfer logs and file transfer requests

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
- `logs/`: Default directory for generated transfer logs
- `requests/`: Default directory for generated file transfer requests
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
