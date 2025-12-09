"""Scaffolding tests for `src/cli/handlers.py`."""

import csv
import datetime
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import cli.handlers as handlers
from constants import REQUEST_LOG_HEADERS


@contextmanager
def _freeze_datetime(fixed_value: datetime.datetime):
    """Patch `cli.handlers.datetime` so timestamps are stable in tests."""

    with patch("cli.handlers.datetime") as mock_datetime:
        mock_datetime.datetime.now.return_value = fixed_value
        mock_datetime.datetime.strptime.side_effect = (
            lambda value, fmt: datetime.datetime.strptime(value, fmt)
        )
        yield


class DummyConfig(SimpleNamespace):
    """Lightweight config stub so CLI handlers can run without a real config file."""

    def get(self, section, option, fallback=None):
        defaults = {
            ("Logging", "OutputFolder"): "./logs",
            ("Requests", "OutputFolder"): "./requests",
            ("Logging", "FileListName"): "{timestamp}_{username}_{transfertype}_{source}-{destination}_FileList.csv",
            ("Logging", "TransferLogName"): "TransferLog_{year}.log",
            ("Requests", "FileListName"): "{date:yyyyMMdd}_{username}_Request_{counter}.csv",
            ("Requests", "RequestLogName"): "RequestLog_{year}.log",
            ("Requests", "EnableRequestLog"): "true",
            ("UI", "LocalNetwork"): "Intranet",
        }
        return defaults.get((section, option), fallback)

    def get_transfer_types(self):
        return {"Low to High": "L2H", "High to High": "H2H", "High to Low": "H2L"}


def _patch_config(dummy=None):  # helper to keep patches consistent
    if dummy is None:
        dummy = DummyConfig()
    return patch.multiple(
        handlers.ConfigManager,
        __init__=lambda self, path: None,
        get_transfer_types=lambda self: dummy.get_transfer_types(),
        get=lambda self, section, option, fallback=None: dummy.get(section, option, fallback),
    )


def test_run_cli_no_valid_files(tmp_path, capsys):
    argv = [
        "main.py",
        "-t",
        "--media-type",
        "Flash",
        "--media-id",
        "TEST-001",
        "--transfer-type",
        "L2H",
        "--source",
        "A",
        "--destination",
        "B",
        "--files",
        str(tmp_path / "missing.txt"),
    ]

    with patch.object(sys, "argv", argv), _patch_config(), patch("cli.handlers.collect_files", return_value=[]):
        handlers.run_cli()

    captured = capsys.readouterr()
    assert "No valid files" in captured.out


def test_run_request_cli_missing_requestor(tmp_path):
    argv = ["main.py", "-r", "--purpose", "Test", "--files", str(tmp_path / "f.txt")]

    with patch.object(sys, "argv", argv), _patch_config():
        with pytest.raises(SystemExit):
            handlers.run_request_cli()


def test_run_request_cli_invalid_date_format(tmp_path, capsys):
    test_file = tmp_path / "data.txt"
    test_file.write_text("content")

    argv = [
        "main.py",
        "-r",
        "--requestor",
        "User",
        "--purpose",
        "Test",
        "--request-date",
        "not-a-date",
        "--files",
        str(test_file),
    ]

    with patch.object(sys, "argv", argv), _patch_config():
        handlers.run_request_cli()

    captured = capsys.readouterr()
    assert "Error" in captured.out and "date" in captured.out


def test_run_cli_generates_file_list_and_log(tmp_path, capsys):
    data_file = tmp_path / "payload.bin"
    data_file.write_bytes(b"abc")
    output_dir = tmp_path / "cli_out"
    fixed_now = datetime.datetime(2025, 1, 2, 3, 4, 5)
    file_list_locations: list[str] = []

    def fake_save(dest_dir, files, file_hashes, progress_signal=None, cancel_check=None):  # pragma: no cover - helper closure
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        target = dest_path / "filelist.csv"
        target.write_text("\n".join(files), encoding="utf-8")
        file_list_locations.append(str(target))
        return str(target)

    argv = [
        "main.py",
        "-t",
        "--media-type",
        "Flash",
        "--media-id",
        "MEDIA-01",
        "--transfer-type",
        "L2H",
        "--source",
        "Src",
        "--destination",
        "Dest",
        "--files",
        str(data_file),
        "--output",
        str(output_dir),
    ]

    with patch.object(sys, "argv", argv), _patch_config(), _freeze_datetime(fixed_now), \
        patch("cli.handlers.collect_files", return_value=[str(data_file)]), \
        patch.object(handlers.TransferLog, "_save_file_list", side_effect=fake_save), \
        patch("cli.handlers.getpass.getuser", return_value="tester"), \
        patch("cli.handlers.socket.gethostname", return_value="CLI-HOST"):
        handlers.run_cli()

    captured = capsys.readouterr()
    assert "Successfully logged 1 files" in captured.out

    year = fixed_now.strftime("%Y")
    log_file = output_dir / f"TransferLog_{year}.log"
    assert log_file.exists()
    assert file_list_locations, "file list should be created"
    saved_file_list = Path(file_list_locations[0])
    assert saved_file_list.exists()

    with log_file.open(newline="", encoding="utf-8") as fp:
        rows = list(csv.reader(fp))

    assert rows[0] == handlers.TRANSFER_LOG_HEADERS
    assert len(rows) == 2
    entry = rows[1]
    assert entry[2] == "tester"
    assert entry[3] == "CLI-HOST"
    assert entry[10] == "1"
    assert entry[-1] == str(saved_file_list)


def test_run_request_cli_creates_request_log_with_hashes(tmp_path, capsys):
    data_file = tmp_path / "request.bin"
    data_file.write_bytes(b"payload")
    output_dir = tmp_path / "req_out"
    fixed_now = datetime.datetime(2025, 4, 5, 6, 7, 8)
    file_list_locations: list[str] = []

    def fake_request_file_list(dest_dir, files, file_hashes, progress_signal, cancel_check):  # pragma: no cover - helper closure
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)
        if progress_signal is not None:
            progress_signal.emit(10)
            progress_signal.emit(100)
        target = dest_path / "request_file.csv"
        target.write_text("\n".join(files), encoding="utf-8")
        file_list_locations.append(str(target))
        return str(target)

    argv = [
        "main.py",
        "-r",
        "--requestor",
        "Alice",
        "--purpose",
        "Testing",
        "--request-date",
        "01/15/2025",
        "--computer-name",
        "CLI-HOST",
        "--files",
        str(data_file),
        "--output",
        str(output_dir),
        "--sha256",
    ]

    with patch.object(sys, "argv", argv), _patch_config(), _freeze_datetime(fixed_now), \
        patch("cli.handlers.collect_files", return_value=[str(data_file)]), \
        patch.object(handlers.RequestLog, "_save_file_list_with_progress", side_effect=fake_request_file_list), \
        patch("cli.handlers.compute_hashes", return_value={str(data_file): "hash"}) as mock_hashes:
        handlers.run_request_cli()

    mock_hashes.assert_called_once()
    captured = capsys.readouterr()
    assert "Successfully created request for 1 files" in captured.out
    assert file_list_locations, "request file list should be created"
    saved_file_list = Path(file_list_locations[0])
    assert saved_file_list.exists()

    year = fixed_now.strftime("%Y")
    request_log_file = output_dir / f"RequestLog_{year}.log"
    assert request_log_file.exists()

    with request_log_file.open(newline="", encoding="utf-8") as fp:
        rows = list(csv.reader(fp))

    assert rows[0] == REQUEST_LOG_HEADERS
    assert len(rows) == 2
    entry = rows[1]
    assert entry[2] == "Alice"
    assert entry[3] == "CLI-HOST"
    assert entry[5] == "1"
    assert entry[-1] == str(saved_file_list)
