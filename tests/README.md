# PyDTATransferLog Test Suite

This directory contains the complete test suite for PyDTATransferLog, organized by test type.

## Structure

```
tests/
├── conftest.py              # Shared pytest fixtures and configuration
├── README.md                # This file - comprehensive testing documentation
├── integration/             # Integration tests (end-to-end functionality)
│   ├── test_cli_functionality.py    # CLI mode testing
│   └── test_functionality.py        # General integration tests
└── unit/                    # Unit tests (isolated component testing)
    ├── test_cli_handlers.py
    ├── test_constants.py
    ├── test_main.py
    ├── models/              # Model-specific unit tests
    │   ├── test_log_and_request_models.py
    │   └── test_review_model.py
    └── utils/               # Utility-specific unit tests
        ├── test_archive_utils.py
        ├── test_cli_utils.py
        ├── test_cli_utils_format_timestamp.py
        ├── test_config_manager.py
        ├── test_file_list_writer.py
        └── test_file_utils.py
```

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Only Unit Tests
```bash
pytest tests/unit/
```

### Run Only Integration Tests
```bash
pytest tests/integration/
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### Run Specific Test File
```bash
pytest tests/unit/models/test_log_and_request_models.py
```

### Run Tests by Marker
```bash
# Run CLI-specific tests
pytest -m cli

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Mock external dependencies
- Fast execution
- High code coverage

### Integration Tests (`tests/integration/`)
- Test end-to-end workflows
- Test CLI functionality with real file operations
- Test cross-component interactions
- Verify actual file creation and content

## Writing New Tests

### Unit Test Example
```python
# tests/unit/utils/test_new_util.py
import pytest
from src.utils.new_util import my_function

def test_my_function_basic():
    """Test basic functionality of my_function."""
    result = my_function("input")
    assert result == "expected_output"

def test_my_function_edge_case():
    """Test edge case handling."""
    with pytest.raises(ValueError):
        my_function(None)
```

### Integration Test Example
```python
# tests/integration/test_new_feature.py
import pytest
import os
from pathlib import Path

def test_end_to_end_workflow(tmp_path):
    """Test complete workflow from input to output."""
    # Setup
    input_file = tmp_path / "input.txt"
    input_file.write_text("test data")
    
    # Execute
    result = run_workflow(input_file)
    
    # Verify
    assert result.success
    assert os.path.exists(result.output_path)
```

## CI/CD Integration

Tests are automatically run on:
- Push to `main`, `develop`, or `feature/*` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

Test matrix includes:
- **Operating Systems**: Windows Latest, Ubuntu Latest
- **Python Versions**: 3.10, 3.11, 3.12, 3.13

## Test Markers

Available pytest markers (defined in `pytest.ini`):
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.gui` - Tests requiring GUI components
- `@pytest.mark.cli` - CLI functionality tests

## Fixtures

Common fixtures are defined in `conftest.py`:
- `tmp_path` - Pytest built-in temporary directory
- `config_manager` - Shared ConfigManager instance
- Custom fixtures as needed

## Coverage Requirements

- Target: 80%+ overall coverage
- Unit tests should achieve high coverage of individual modules
- Integration tests verify critical user workflows
- Coverage reports are generated in CI and uploaded as artifacts

## Debugging Tests

### Run with Verbose Output
```bash
pytest tests/ -v
```

### Run with Detailed Traceback
```bash
pytest tests/ --tb=long
```

### Run Specific Test Function
```bash
pytest tests/unit/utils/test_file_utils.py::test_specific_function -v
```

### Run and Stop at First Failure
```bash
pytest tests/ -x
```

### Run with Print Statements Visible
```bash
pytest tests/ -s
```

## Best Practices

1. **Test Naming**: Use descriptive names starting with `test_`
2. **Isolation**: Unit tests should not depend on each other
3. **Cleanup**: Use fixtures and context managers for proper cleanup
4. **Assertions**: Use clear, specific assertions with helpful messages
5. **Documentation**: Add docstrings explaining what each test verifies
6. **Parametrization**: Use `@pytest.mark.parametrize` for testing multiple inputs
7. **Mocking**: Mock external dependencies in unit tests
8. **File Operations**: Use `tmp_path` fixture for file-based tests

## Troubleshooting

### Tests Fail on Windows but Pass on Linux
- Check path separator usage (`os.path.join()` vs string concatenation)
- Verify line ending handling (`newline=''` in file operations)
- Test file permissions and case sensitivity

### Import Errors
```bash
# Ensure src is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# Or on Windows PowerShell
$env:PYTHONPATH="$env:PYTHONPATH;$(Get-Location)"
```

### GUI Tests Fail in CI
- GUI tests require display server (Xvfb on Linux)
- Use `@pytest.mark.gui` marker and `continue-on-error` in CI
- Consider headless testing or mocking GUI components
