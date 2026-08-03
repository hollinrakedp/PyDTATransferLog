# PyDTATransferLog Copilot Instructions
- **Path Resolution**: All relative paths in config files are resolved relative to the Python script (`src/main.py`) or binary executable location, not the current working directory
- **CLI Path Behavior**: CLI `--output` paths are resolved relative to the user's current working directory for better CLI UX; config defaults remain relative to the application location

## Architecture Overview

PyDTATransferLog is a PySide6-based cross-platform file transfer loggin**Post-Execution Validation**
After running CLI commands, verify:
1. **File Creation**: Check that log/request files are created in expected locations
2. **File Naming**: Verify filename follows configured naming pattern
3. **Content Validation**: Ensure CSV content matches expected format and includes all specified files
4. **Directory Structure**: Confirm year-based subdirectories are created properly
5. **Permission Handling**: Test with restricted directories and invalid paths
6. **Checksum Verification**: When `--sha256` is used, verify checksums are calculated and stored
7. **Working Directory**: CLI `--output` paths are now relative to the user's current working directory for standard CLI behavior
8. **Path Resolution**: Config file relative paths resolve from script/executable location, CLI paths from user's CWDy with both GUI and CLI modes. The application tracks file transfers between different security domains/networks with detailed metadata, checksums, and archive content inspection.

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
5. **Path Resolution**: All relative paths in config files are resolved relative to the Python script (`src/main.py`) or binary executable location, not the current working directory

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

### CLI Testing Framework

**Critical**: Always test both CLI modes after making changes to file processing, configuration, or argument parsing.

#### Transfer Logging CLI Tests
```bash
# Basic transfer logging
python src/main.py -t --media-type "Flash" --media-id "CN-123-456" --transfer-type "L2H" --source "Intranet" --destination "Customer" --files file1.txt file2.txt

# Transfer with folders and checksums
python src/main.py -t --media-type "HDD" --media-id "EXT-500GB" --transfer-type "H2H" --source "System1" --destination "System2" --files document.pdf --folders ./test_folder --sha256

# Test all transfer types from config
python src/main.py -t --media-type "SSD" --media-id "CN-789" --transfer-type "Low to High" --source "Workstation" --destination "Server" --files README.md
python src/main.py -t --media-type "SSD" --media-id "CN-789" --transfer-type "L2H" --source "Workstation" --destination "Server" --files README.md

# Test with custom output directory
python src/main.py -t --media-type "Flash" --media-id "TEST-001" --transfer-type "L2H" --source "TestSrc" --destination "TestDest" --files version.txt --output ./test_logs

# Error conditions to test
python src/main.py -t --media-type "InvalidType" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files nonexistent.txt
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "InvalidType" --source "A" --destination "B" --files README.md
```

#### Request Generation CLI Tests
```bash
# Basic request generation
python src/main.py -r --requestor "TestUser" --purpose "Testing CLI request functionality" --files file1.txt file2.txt

# Request with folders and checksums
python src/main.py -r --requestor "Jane Doe" --purpose "Data analysis files for project" --files analysis.xlsx --folders ./data --sha256

# Request with custom date and computer name
python src/main.py -r --requestor "John Smith" --purpose "System configuration backup" --request-date "12/15/2025" --computer-name "WORKSTATION-01" --files config.ini

# Request with custom output directory
python src/main.py -r --requestor "Test Requestor" --purpose "Testing custom output" --files README.md --output ./test_requests

# Error conditions to test
python src/main.py -r --purpose "Missing requestor test" --files README.md
python src/main.py -r --requestor "Test User" --files nonexistent.txt
python src/main.py -r --requestor "Test User" --purpose "Invalid date test" --request-date "invalid-date" --files README.md
```

#### Version and Help Testing
```bash
# Version information
python src/main.py -V
python src/main.py --version

# Help for each mode
python src/main.py -h
python src/main.py --help
python src/main.py -t --help
python src/main.py -r --help
```

#### Cross-Platform CLI Testing
```bash
# Test with different path formats (Windows)
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files "C:\Windows\System32\notepad.exe"

# Test with different path formats (Unix-style on Windows)
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files "/c/temp/file.txt"

# Test with quoted paths containing spaces
python src/main.py -r --requestor "Test User" --purpose "Quoted path test" --files "file with spaces.txt"
```

#### Configuration Validation Testing
```bash
# Test transfer type validation against config
# Ensure these match exactly what's in config.ini [UI] TransferTypes
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files README.md
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "Low to High" --source "A" --destination "B" --files README.md

# Test media type validation against config  
# Ensure these match exactly what's in config.ini [UI] MediaTypes
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files README.md
python src/main.py -t --media-type "HDD" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files README.md
```

#### Post-Execution Validation
After running CLI commands, verify:
1. **File Creation**: Check that log/request files are created in expected locations
2. **File Naming**: Verify filename follows configured naming pattern
3. **Content Validation**: Ensure CSV content matches expected format and includes all specified files
4. **Directory Structure**: Confirm year-based subdirectories are created properly
5. **Permission Handling**: Test with restricted directories and invalid paths
6. **Checksum Verification**: When `--sha256` is used, verify checksums are calculated and stored

#### Error Handling Validation
Test that CLI gracefully handles:
- Missing required arguments
- Invalid file paths
- Insufficient permissions
- Invalid configuration values
- Network path issues
- Large file processing
- Archive file processing errors

### Configuration System

The `ConfigManager` class provides the foundation for all UI behavior:

- **Media Types**: `MediaTypes = Apricorn, Blu-ray, CD, DVD, Flash, HDD, microSD, SD, SSD`
- **Transfer Types**: `TransferTypes = Low to High:L2H, High to High:H2H, High to Low:H2L`
- **File Naming**: Uses token replacement system (e.g., `{date:yyyyMMdd}_{username}_{transfertype}_{direction}_{source}-{destination}_{counter}.csv`)

**Critical**: Always use `config.get_transfer_types()` for transfer type validation in CLI mode.

## Cross-Platform Compatibility Guidelines

### Core Principles

PyDTATransferLog must maintain compatibility across Windows and Linux systems. All new features and implementations must adhere to cross-platform best practices.

#### Path Handling Requirements

**Always use these functions for path operations:**
```python
import os

# Path normalization (REQUIRED for all file paths)
normalized_path = os.path.normcase(os.path.normpath(os.path.abspath(file_path)))

# Path joining (NEVER use string concatenation)
full_path = os.path.join(base_dir, filename)

# Path expansion (for user paths like ~)
expanded_path = os.path.expanduser(user_path)

# Path existence checking
if os.path.exists(file_path):
    # Process file
```

**Forbidden Practices:**
```python
# ❌ NEVER do string concatenation for paths
bad_path = directory + "/" + filename
bad_path = directory + "\\" + filename

# ❌ NEVER assume path separators
bad_path = "logs\\2025\\file.csv"  # Breaks on Linux
bad_path = "logs/2025/file.csv"    # May break on Windows

# ❌ NEVER assume drive letters exist
bad_path = "C:\\temp\\file.txt"    # Breaks on Linux
```

#### File Operations Requirements

**Use these patterns for file operations:**
```python
# File reading with proper encoding
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# CSV operations with proper newline handling
with open(file_path, 'r', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)

with open(file_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

# Directory creation (cross-platform)
os.makedirs(directory_path, exist_ok=True)

# File dialog operations (Qt handles cross-platform automatically)
file_path, _ = QFileDialog.getOpenFileName(
    parent, caption, start_dir, file_filter
)
```

#### Configuration and Resource Handling

**Path resolution patterns:**
```python
# Resource path resolution (PyInstaller compatible)
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)
```

**Critical Path Resolution Behavior:**
All relative paths in `config.ini` are resolved relative to the application's executable location:
- **Development mode**: Relative to `src/main.py` location
- **Binary mode**: Relative to the executable (`.exe`) location  
- **Config paths**: `./logs`, `./requests` resolve from the script/binary directory, NOT the current working directory
- **GUI mode**: Output paths follow config file behavior (relative to application location)
- **CLI mode**: `--output` paths are relative to current working directory for standard CLI behavior
- **Current CLI behavior**: `--output ./test` creates `test/` relative to current working directory (user-friendly)
- **Config defaults**: When no `--output` specified, uses config paths relative to application location

### Testing Requirements

**Every new feature MUST be tested on:**
1. **Windows 11** with both forward and backslash paths
2. **Linux** (Ubuntu/RHEL) with case-sensitive filesystem considerations
3. **Mixed environments** where files are created on one OS and accessed on another

**Path Testing Checklist:**
- [ ] Relative paths work correctly
- [ ] Absolute paths work correctly  
- [ ] Paths with spaces work correctly
- [ ] Unicode characters in paths work correctly
- [ ] Network paths work correctly (Windows UNC, Linux mounts)
- [ ] Long path names work correctly
- [ ] Case sensitivity differences are handled

### UI Framework Considerations

**PySide6/Qt Cross-Platform Guidelines:**
```python
# File dialogs (automatically cross-platform)
QFileDialog.getOpenFileName()
QFileDialog.getSaveFileName()
QFileDialog.getExistingDirectory()

# Path display in UI (normalize for display)
display_path = os.path.normpath(file_path)

# Icon and resource loading (use Qt resource system or proper path resolution)
icon_path = get_resource_path("resources/icons/icon.png")
```

### Error Handling Patterns

**Cross-platform error handling:**
```python
try:
    # File operation
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except (OSError, IOError, PermissionError) as e:
    # Handle both Windows and Linux specific errors
    logger.error(f"Error accessing file {file_path}: {str(e)}")
    return None
except UnicodeDecodeError as e:
    # Handle encoding issues
    logger.error(f"Encoding error reading {file_path}: {str(e)}")
    return None
```

### Development Environment Setup

**Cross-platform development requirements:**
1. **Virtual Environment**: Always use virtual environments
2. **Dependencies**: Keep requirements.txt updated with version constraints
3. **Line Endings**: Configure git to handle line endings properly
4. **Testing**: Test on both platforms before committing

**Git Configuration for Cross-Platform:**
```bash
# Set line ending handling
git config core.autocrlf true    # Windows
git config core.autocrlf input   # Linux/Mac
```

## File Organization Patterns

### Log Structure
```
logs/
├── TransferLog_2025.log          # Annual summary CSV
└── 2025/                         # Year-based file lists
    ├── 20250429_Darren_L2H_Incoming_Intranet-Customer_001.csv
    └── 20250429_Darren_L2H_Outgoing_Intranet-Customer_001.csv
```

### Request Structure
```
requests/
├── RequestLog_2025.log           # Annual request summary CSV
└── 2025/                         # Year-based request files
    ├── 20250429_Darren_Request_001.csv
    ├── 20250429_Darren_Request_002.csv
    └── 20250429_JohnDoe_Request_001.csv
```

### Source Structure
- `src/constants.py` - CSV headers and display constants
- `src/models/log_model.py` - Core `TransferLog` class with file processing
- `src/models/request_model.py` - Request handling and CSV generation
- `src/ui/app_window.py` - Main tabbed window container
- `src/ui/log_window.py` - File transfer logging interface
- `src/ui/request_window.py` - File transfer request interface
- `src/ui/review_window.py` - Log review and search interface
- `src/utils/archive_utils.py` - Archive inspection and content listing
- `src/utils/config_manager.py` - Configuration file management
- `src/utils/file_utils.py` - File operations and metadata collection

## Key Implementation Details

### File Processing
- Files are processed through `FileInfo` dataclass for metadata collection
- Archive inspection uses built-in libraries (zipfile, tarfile) for content listing
- SHA-256 checksums are optional and processed in chunks for large files
- Drag-and-drop support in GUI for files and folders
- **Import Request Functionality**: Log tab supports importing file lists from multiple formats:
  - CSV files (request files generated by the application)
  - Plain text files (one file path per line, supports comments and quoted paths)
  - Auto-detection for unknown file extensions
  - Cross-platform path normalization and missing file handling
  - Warning system for mixed file sources with user control options

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
5. **Cross-Platform**: Test file dialogs and path handling on both Windows and Linux
6. **Cross-Platform**: Use `os.path.join()` for all path construction
7. **Cross-Platform**: Normalize all user-provided paths with `os.path.normpath()`

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
5. **Import Request Files**: Test import functionality with both CSV and text formats
   - CSV files should parse with `_parse_csv_request_file()` method
   - Text files should parse with `_parse_text_file_list()` method
   - Auto-detection should work via `_parse_auto_detect_file()` method
   - Test path normalization across platforms
   - Verify missing file handling and warning dialogs
6. **CLI Compatibility**: After implementing GUI import features, verify CLI modes still work:
   - Test transfer logging CLI with various file combinations
   - Test request generation CLI with various file combinations  
   - Ensure import functionality doesn't interfere with CLI argument parsing
   - Verify file processing methods work consistently between GUI and CLI modes
7. **Cross-Platform**: Use proper path normalization for all file operations:
   - Apply `os.path.normcase(os.path.normpath(os.path.abspath(path)))` to all paths
   - Test with Windows paths (C:\folder\file.txt) and Unix paths (/home/user/file.txt)
   - Handle quoted paths and paths with spaces correctly
   - Verify network paths work (Windows UNC and Linux mounts)

When adding CLI arguments:
1. Update argument parser in `run_cli()` function
2. Validate against config-driven options using `get_transfer_types()`
3. Maintain compatibility with existing log naming patterns
4. Test both short and long transfer type specifications
5. **CLI Path Handling**: Consider making CLI `--output` paths relative to current working directory (not script location) for better UX

## Testing Methodology

### CLI Testing Best Practices

**Always test CLI functionality after any changes to:**
- File processing logic (`models/log_model.py`, `models/request_model.py`)
- Configuration handling (`utils/config_manager.py`)
- Argument parsing (`main.py` CLI sections)
- Path normalization or file operations
- CSV generation or parsing

**Automated Testing Framework**

### GitHub Actions Integration

The project includes comprehensive automated testing via GitHub Actions in `.github/workflows/build.yaml`:

**Test Matrix:**
- **Operating Systems**: Windows Latest, Ubuntu Latest
- **Python Versions**: 3.10, 3.11, 3.12, 3.13
- **Test Types**: Unit tests, integration tests, CLI functionality, cross-platform compatibility

**Test Workflow:**
1. **Linting**: ruff for code quality and syntax (replaces flake8/isort/pycodestyle)
2. **Type Checking**: mypy for type validation (continue-on-error)
3. **Comprehensive Testing**: pytest suite covering CLI, import, config, paths
4. **GUI Testing**: Headless GUI startup verification (blocking)
5. **Coverage**: pytest-cov produces HTML and summary in CI (no threshold enforced yet)
6. **Build Testing**: Executable creation and validation
7. **Cross-Platform Validation**: Path handling and file operations

### Artifacts and Versions

- CI artifacts are versioned using short semver plus commit hash for traceability.
- Coverage reports are uploaded as CI artifacts (HTML + summary).

### Running Tests Locally

**Quick Test Suite:**
```bash
# Run CLI-focused tests quickly
python -m pytest tests/test_cli_functionality.py

# Run individual test components
python -m pytest test_cross_platform.py
python -m pytest test_import_formats.py
```

**Full Test Suite (with pytest):**
```bash
# Install testing dependencies
pip install pytest pytest-cov ruff mypy

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

**Manual Testing:**
```bash
# Test CLI functionality
python src/main.py --version
python src/main.py -t --help
python src/main.py -r --help

# Test basic operations
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files README.md
python src/main.py -r --requestor "Test" --purpose "Testing" --files README.md
```
### Running Tests Locally

**Quick Test Suite:**
```bash
# Run CLI-focused tests quickly
python -m pytest tests/test_cli_functionality.py

# Run individual test components
python -m pytest test_cross_platform.py
python -m pytest test_import_formats.py
```

**Full Test Suite (with pytest):**
```bash
# Install testing dependencies
pip install pytest pytest-cov ruff mypy

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

**Manual Testing:**
```bash
# Test CLI functionality
python src/main.py --version
python src/main.py -t --help
python src/main.py -r --help

# Test basic operations
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files README.md
python src/main.py -r --requestor "Test" --purpose "Testing" --files README.md
```

### Running Tests Locally

**Quick Test Suite:**
```bash
# Run comprehensive CLI tests (no external dependencies)
python tests/test_cli_functionality.py

# Run individual test components
python test_cross_platform.py
python test_import_formats.py
```

**Full Test Suite (with pytest):**
```bash
# Install testing dependencies
pip install pytest pytest-cov flake8 mypy

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

**Manual Testing:**
```bash
# Test CLI functionality
python src/main.py --version
python src/main.py -t --help
python src/main.py -r --help

# Test basic operations
python src/main.py -t --media-type "Flash" --media-id "TEST" --transfer-type "L2H" --source "A" --destination "B" --files README.md
python src/main.py -r --requestor "Test" --purpose "Testing" --files README.md
```

### Test Structure

**Test Files:**
- `tests/test_cli_functionality.py` - Comprehensive CLI and functionality tests (no external deps)
- `tests/test_functionality.py` - Unit tests with pytest framework
- `test_cross_platform.py` - Cross-platform compatibility validation
- `test_import_formats.py` - Import functionality testing
- `pytest.ini` - Pytest configuration

**Testing Requirements:**
- Tests must run without GUI dependencies
- CLI tests must verify actual file creation and content
- Cross-platform tests must validate path normalization
- Import tests must verify CSV and text file parsing
- Configuration tests must validate loading and parsing

### Continuous Integration

**Trigger Conditions:**
- Push to main, develop, or feature/* branches
- Pull requests to main or develop
- Manual workflow dispatch

**Quality Gates:**
- All tests must pass on both Windows and Linux
- CLI functionality must work across Python versions
- Build artifacts must be successfully created
- Executables must run basic commands without errors

**Failure Handling:**
- Linting failures are non-blocking (continue-on-error)
- Type checking failures are non-blocking
- GUI tests are non-blocking (for headless environments)
- Core functionality tests are blocking (will fail the build)