# Request Import Feature

## Overview

The **Request Import** feature allows users to import files and metadata from previously generated request CSV files directly into the log tab for file transfer logging. This streamlines the workflow from request creation to transfer logging.

## How It Works

### Location

- **UI Location**: Log tab, in the file selection button area
- **Button**: "Import Request" button (positioned between "Remove Selected" and "Select Files")
- **Menu**: File → Import Request... (Ctrl+I)

### Import Process

1. **File Selection**: Click "Import Request" or use Ctrl+I to open a file dialog
2. **Request Parsing**: The system automatically:
   - Locates the corresponding request log entry
   - Extracts metadata (requestor, date, purpose, etc.)
   - Parses the file list from the CSV
3. **Data Population**: User is prompted to import metadata into log form fields
4. **File Import**: All level-0 files (top-level files, not archive contents) are added to the file selection list

### What Gets Imported

#### Files (Automatic)

- All top-level files (Level=0) from the request file list
- Archive contents (Level=1+) are filtered out since they don't represent actual transferable files
- Missing files are reported but don't stop the import process

#### Metadata (Reference Only)

The import process displays request metadata for reference but does **not** populate form fields:

- **Requestor**: Shown for reference (transfer may be done by different user)
- **Request Date**: Shown for reference (transfer may happen on different date)
- **Purpose**: Shown for reference (provides context for the transfer)
- **Computer Name**: Shown for reference

**Rationale**: Request and transfer are separate events that typically occur at different times and may involve different personnel. All transfer-specific details should be entered manually to ensure accuracy.

### File Structure Requirements

The import feature expects the standard request file structure:

```
requests/
├── RequestLog_YYYY.log          # Annual request summary
└── YYYY/                        # Year-based request files
    └── YYYYMMDD_User_Request_NNN.csv
```

### CSV Format Compatibility

#### Request Log (RequestLog_YYYY.log)

```csv
"Timestamp","Request Date","Requestor","Computer Name","Purpose","File Count","Total Size","File Log"
```

#### Request File List (YYYYMMDD_User_Request_NNN.csv)

```csv
"Level","Container","FullName","Size","File Hash"
"0","","C:/path/to/file1.txt","1024",""
"0","","C:/path/to/file2.txt","2048",""
"1","C:/path/to/archive.zip","internal_file.txt","512",""
```

Only Level=0 entries are imported as transferable files.

## User Experience

### Success Scenario

1. User clicks "Import Request"
2. Selects a request CSV file
3. Sees information dialog with request details (for reference only)
4. Confirms file import
5. Files are automatically added to the file list
6. Success message shows imported file count
7. User manually enters appropriate transfer details (date, user, etc.)

### Error Handling

- **Missing request log**: Files are still imported, but no metadata is available
- **Missing files**: User is notified of files that couldn't be found on disk
- **Invalid CSV format**: Clear error message with details
- **No files found**: Warning if the request contains no importable files
- **Mixed file sources**: Warning when existing selected files are not in the request being imported

### Visual Feedback

- Status bar updates during import process
- Progress indication for file validation
- Clear success/error messages
- File count updates in real-time
- Warning dialogs for potential file conflicts

## Mixed File Sources Warning

### When It Appears

The system displays a warning dialog when:

- Files are already selected in the log tab
- A request is being imported
- Some existing files are NOT included in the request

### Warning Dialog Example

```
Mixed File Sources Warning

Warning: You have 15 existing file(s) selected that are NOT in this request:

• report.pdf
• very_long_filename_that_should_be_truncated....pdf
• extremely_long_filename_with_multiple_unde....docx
• ... and 12 more

These files will remain selected along with the 3 request files.
This means your transfer will include files from multiple sources.

How would you like to proceed?

[Keep All Files] [Remove Non-Request Files] [Cancel Import]
```

### Smart Handling of Large File Lists

- **Limited Display**: Shows only first 3 files to keep dialog manageable
- **Filename Truncation**: Long filenames (>50 chars) are truncated with "..." while preserving file extensions
- **Count Summary**: Clear indication of how many additional files exist
- **Dialog Size**: Maintains reasonable dialog width regardless of filename length

### User Options

- **Keep All Files**: Continue with import, keeping both existing and request files (mixed sources)
- **Remove Non-Request Files**: Remove existing files that aren't in the request, then import request files (clean import)  
- **Cancel Import**: Cancel the import operation and keep current file selection unchanged

### Dialog Features

- **Clear Tooltips**: Each button has explanatory tooltip text
- **Safe Default**: "Cancel Import" is the default button for safety
- **Smart Layout**: Options ordered from least to most destructive
- **Visual Clarity**: Warning icon and clear messaging

This three-option approach gives users complete control over how to handle file conflicts, supporting both mixed-source workflows and clean request-only imports.

## Technical Implementation

### Key Methods

- `import_request_file()`: Main import workflow with user interaction
- `_parse_request_file()`: Core parsing logic for CSV files
- File validation and existence checking
- Metadata extraction and form population

### Integration Points

- Shares file addition logic with existing drag-drop and file selection
- Uses standard configuration paths for request folder location
- Maintains compatibility with existing file processing workflows

## Benefits

1. **Workflow Efficiency**: Eliminates manual file re-selection after creating requests
2. **File Accuracy**: Ensures exact same files from request are transferred
3. **Time Savings**: Faster transition from request to logging phases
4. **User Experience**: Intuitive integration with existing interface patterns
5. **Transfer Integrity**: Maintains separation between request and transfer events
6. **Error Reduction**: Automated file validation and missing file reporting

## Configuration

The feature uses existing configuration settings:

- `[Requests] OutputFolder`: Default location for request file dialog
- Standard file dialog filters for CSV files
- No additional configuration required

## Keyboard Shortcuts

- **Ctrl+I**: Import Request (menu and button)
- Works alongside existing shortcuts (Ctrl+O for files, Ctrl+D for folders, etc.)

## Compatibility

- Compatible with all existing request file formats
- Works with both GUI and future CLI modes
- Maintains backward compatibility with existing workflows
- No changes to file output formats or structures
