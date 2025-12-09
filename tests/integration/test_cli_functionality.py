#!/usr/bin/env python3
"""CLI functionality tests (pytest style)."""

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))
PYTHON = sys.executable

from utils.config_manager import ConfigManager  # noqa: E402


def run_cli(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run CLI with list args relative to repo root."""
    return subprocess.run(
        [PYTHON] + args,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

def test_version_and_help():
    cases = [
        ["src/main.py", "--version"],
        ["src/main.py", "--help"],
        ["src/main.py", "-V"],
        ["src/main.py", "-h"],
        ["src/main.py", "-t", "--help"],
        ["src/main.py", "-r", "--help"],
    ]
    for args in cases:
        result = run_cli(args)
        assert result.returncode == 0, result.stderr

def test_config_loading():
    config = ConfigManager()
    media_types = config.get_media_types()
    transfer_types = config.get_transfer_types()

    assert "Flash" in media_types
    if isinstance(transfer_types, dict):
        assert "Low to High" in transfer_types or "L2H" in transfer_types.values()
    else:
        assert any("L2H" in str(t) for t in transfer_types)

def test_cli_functionality(tmp_path: Path):
    test_file = tmp_path / "test_file.txt"
    test_folder = tmp_path / "test_folder"
    test_folder.mkdir()

    test_file.write_text("Test file content for CLI testing", encoding="utf-8")
    (test_folder / "folder_file.txt").write_text("Test folder file content", encoding="utf-8")

    transfer_args = [
        "src/main.py",
        "-t",
        "--media-type",
        "Flash",
        "--media-id",
        "TEST-001",
        "--transfer-type",
        "L2H",
        "--source",
        "TestSrc",
        "--destination",
        "TestDest",
        "--files",
        str(test_file),
        "--folders",
        str(test_folder),
        "--output",
        str(tmp_path / "logs"),
    ]
    result = run_cli(transfer_args)
    assert result.returncode == 0, result.stderr

    request_args = [
        "src/main.py",
        "-r",
        "--requestor",
        "CI Test",
        "--purpose",
        "Automated testing",
        "--files",
        str(test_file),
        "--folders",
        str(test_folder),
        "--output",
        str(tmp_path / "requests"),
    ]
    result = run_cli(request_args)
    assert result.returncode == 0, result.stderr

def test_import_functionality(tmp_path: Path):
    csv_file = tmp_path / "test_request.csv"
    csv_file.write_text(
        "Level,Container,FullName,Size,File Hash\n"
        "0,,/test/file1.txt,1024,\n"
        "0,,/test/file2.txt,2048,\n",
        encoding="utf-8",
    )

    text_file = tmp_path / "test_list.txt"
    text_file.write_text(
        "# Test file list\n"
        "/test/file1.txt\n"
        '"/test/file with spaces.txt"\n'
        "# Comment\n"
        "/test/file2.txt\n",
        encoding="utf-8",
    )

    with csv_file.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    level_0_files = [row for row in rows if row.get("Level") == "0"]
    assert len(level_0_files) == 2

    with text_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    file_paths = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            file_paths.append(line)

    assert len(file_paths) == 3
    assert "/test/file with spaces.txt" in file_paths

def test_cross_platform_paths():
    test_paths = [
        "test/path/file.txt",
        "test\\path\\file.txt",
        "./test/path/file.txt",
        "../test/path/file.txt",
    ]

    for path in test_paths:
        normalized = os.path.normpath(os.path.abspath(path))
        assert os.path.isabs(normalized)

    joined = os.path.join("base", "path", "file.txt")
    assert joined.endswith(os.path.join("path", "file.txt"))

def test_transfer_log_csv_validation(tmp_path: Path):
    test_files = []
    for i in range(3):
        test_file = tmp_path / f"test_file_{i}.txt"
        content = f"Test file {i} content for transfer logging" * 10
        test_file.write_text(content, encoding="utf-8")
        test_files.append(test_file)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    transfer_args = [
        "src/main.py",
        "-t",
        "--media-type",
        "Flash",
        "--media-id",
        "TEST-CSV-001",
        "--transfer-type",
        "L2H",
        "--source",
        "TestSource",
        "--destination",
        "TestDest",
        "--files",
        *[str(f) for f in test_files],
        "--output",
        str(output_dir),
    ]

    result = run_cli(transfer_args)
    assert result.returncode == 0, result.stderr

    found_csv = False
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".csv") and not file.endswith(".log"):
                csv_path = Path(root) / file
                with csv_path.open("r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                assert rows, "CSV file is empty"
                expected_headers = {"Level", "Container", "FullName", "Size", "File Hash"}
                actual_headers = set(reader.fieldnames) if reader.fieldnames else set()
                assert expected_headers.issubset(actual_headers)

                file_entries = [row for row in rows if row.get("Level") == "0"]
                assert len(file_entries) == len(test_files)

                csv_paths = {row.get("FullName") for row in file_entries}
                for test_file in test_files:
                    normalized_path = os.path.normpath(test_file)
                    assert any(normalized_path in csv_path or str(test_file) in csv_path for csv_path in csv_paths)

                found_csv = True
                break
        if found_csv:
            break

    assert found_csv, "No transfer log CSV file generated"