# PyDTATransferLog Copilot Instructions

## Architecture Overview

PyDTATransferLog is a PySide6-based cross-platform file transfer logging utility with both GUI and CLI modes. The application tracks file transfers between different security domains/networks with detailed metadata, checksums, and archive content inspection.

### Core Components

- **Entry Point**: `src/main.py` - Dual mode launcher (GUI or CLI with `-c` flag)
- **Configuration**: `src/config.ini` - INI-based config with UI dropdowns and logging templates
- **Models**: `src/models/log_model.py` - `TransferLog` class handles CSV generation and file processing
- **UI**: Tabbed interface with separate logging and review windows (`src/ui/`)
- **Utils**: Config management, file operations, and hash calculations (`src/utils/`)

### Key Architectural Patterns

1. **Dual Execution Modes**: Check `if len(sys.argv) > 1 and sys.argv[1] in ["-c", "--cli"]` in main
2. **PyInstaller Compatibility**: All path resolution uses `sys._MEIPASS` detection for bundled resources
3. **Working Directory Management**: App always changes to script/exe directory on startup
4. **Configuration-Driven UI**: Dropdowns, transfer types, and naming patterns from `config.ini`

## Development Workflow

### Running the Application
```bash
# GUI mode (default)
python src/main.py

# Transfer CLI mode (logging file transfers)
python src/main.py -t --media-type "Flash" --media-id "CN-123-456" --transfer-type "L2H" --source "Intranet" --destination "Customer" --files file1.txt --sha256

# Request CLI mode (generating file transfer requests)
python src/main.py -r --requestor "TestUser" --purpose "Testing request functionality" --files file1.txt --sha256

# GUI mode with specific starting tab
python src/main.py --tab request    # or --tab 0
python src/main.py --tab log        # or --tab 1
python src/main.py --tab review     # or --tab 2

# Version information
python src/main.py -V
python src/main.py --version
```

### Building Executables
```bash
# Use the provided spec file (includes resources and config)
# This creates TWO executables:
pyinstaller main.spec

# Results in dist/ folder:
# - dtatransferlog.exe      (GUI version, console=False)
# - dtatransferlog-cli.exe  (CLI version, console=True)

# Manual build (less preferred)
pyinstaller --name="PyDTATransferLog" --windowed --icon=src/resources/dtatransferlog.ico --add-data="src/resources;resources" src/main.py
```

**Important**: CLI functionality requires the console version (`dtatransferlog-cli.exe`) because the GUI version is compiled with `console=False` and cannot display CLI output in terminal windows.

### Configuration System

The `ConfigManager` class provides the foundation for all UI behavior:

- **Media Types**: `MediaTypes = Apricorn, Blu-ray, CD, DVD, Flash, HDD, microSD, SD, SSD`
- **Transfer Types**: `TransferTypes = Low to High:L2H, High to High:H2H, High to Low:H2L`
- **File Naming**: Uses token replacement system (e.g., `{date:yyyyMMdd}_{username}_{transfertype}_{direction}_{source}-{destination}_{counter}.csv`)

**Critical**: Always use `config.get_transfer_types()` for transfer type validation in CLI mode.

## File Organization Patterns

### Log Structure
```
logs/
├── TransferLog_2025.log          # Annual summary CSV
└── 2025/                         # Year-based file lists
    ├── 20250429_Darren_L2H_Incoming_Intranet-Customer_001.csv
    └── 20250429_Darren_L2H_Outgoing_Intranet-Customer_001.csv
```

### Source Structure
- `src/constants.py` - CSV headers and display constants
- `src/models/log_model.py` - Core `TransferLog` class with file processing
- `src/ui/app_window.py` - Main tabbed window container
- `src/ui/log_window.py` - File transfer logging interface
- `src/ui/review_window.py` - Log review and search interface

## Key Implementation Details

### File Processing
- Files are processed through `FileInfo` dataclass for metadata collection
- Archive inspection uses built-in libraries (zipfile, tarfile) for content listing
- SHA-256 checksums are optional and processed in chunks for large files
- Drag-and-drop support in GUI for files and folders

### Transfer Direction Logic
- Direction (Incoming/Outgoing) determined by comparing source/destination to `LocalNetwork` config
- Transfer types have both full names and abbreviations (e.g., "Low to High:L2H")
- Media ID supports prefixes from config for organizational consistency

### Tab Structure
Current tab order (critical for CLI `--tab` option):
- **Index 0**: Request tab (`FileTransferRequestTab`) - File transfer request generation
- **Index 1**: Log tab (`FileTransferLoggerTab`) - File transfer logging interface  
- **Index 2**: Review tab (`TransferLogReviewerTab`) - Log review and search interface

**Important**: When adding/removing/reordering tabs, update both `app_window.py` and `parse_tab_argument()` in `main.py`

### CSV Output Format
Two CSV types generated:
1. **Annual Log** (`TransferLog_YYYY.log`): Summary with metadata and file list reference
2. **File Lists** (`YYYYMMDD_User_Type_Direction_Source-Dest_NNN.csv`): Detailed file inventory

### Resource Handling
- Icons and stylesheets bundled in `src/resources/`
- Theme system supports custom QSS stylesheets (kaleidoscope-light/dark)
- PyInstaller bundles resources using `--add-data` pattern

## Common Patterns

When adding new UI features:
1. Add configuration options to `config.ini` first
2. Update `ConfigManager` methods for new config sections
3. Use `config.get_list()` for comma-separated dropdown values
4. Maintain PyInstaller resource path compatibility

When adding new tabs to the UI:
1. **Add tab to `app_window.py`**: Use `self.tab_widget.addTab(tab_instance, "Tab Name")` in the correct order
2. **Update CLI tab mapping**: Modify `parse_tab_argument()` function in `main.py`:
   - Update the numeric range validation (e.g., `if 0 <= tab_num <= 3` for 4 tabs)
   - Add new tab name to the `tab_map` dictionary (e.g., `'newtab': 3`)
   - Update help text in argument parser (e.g., `"Starting tab (0/1/2/3 or request/log/review/newtab)"`)
   - Update warning message with valid options
3. **Test both GUI and CLI**: Ensure `--tab` option works with both numeric and named references
4. **Update documentation**: Include new tab in examples and help text

When modifying file processing:
1. Update `FileInfo` dataclass for new metadata
2. Modify CSV headers in `constants.py`
3. Test both GUI drag-drop and CLI file specification
4. Ensure archive content inspection still works

When adding CLI arguments:
1. Update argument parser in `run_cli()` function
2. Validate against config-driven options using `get_transfer_types()`
3. Maintain compatibility with existing log naming patterns
4. Test both short and long transfer type specifications