import csv
import os
from types import SimpleNamespace
from models.base_model import BaseLogModel
from models.log_model import TransferLog
from models.request_model import RequestLog
from utils.file_utils import FileInfo


class DummyConfig(SimpleNamespace):
    def get(self, section, option, fallback=None):
        return fallback


def test_base_log_model_tracks_files(tmp_path):
    model = BaseLogModel(DummyConfig(), "20250101-010101", "HOST", total_size=2048)
    sample = tmp_path / "example.txt"
    sample.write_text("data")

    info = FileInfo(str(sample), size=len("data"))
    model.add_file(info)

    assert model.file_count == 1
    assert model.files[0].name == "example.txt"
    model.total_size = 2048
    assert model.format_total_size() == "2.00 KB"


def test_transfer_log_save_creates_log_and_list(tmp_path):
    config = DummyConfig()
    transfer = TransferLog(
        config=config,
        timestamp="20250101-010203",
        transfer_date="01/01/2025",
        username="tester",
        computer_name="HOST",
        media_type="Flash",
        media_id="ID123",
        transfer_type="L2H",
        source="A",
        destination="B",
        file_count=1,
        total_size=4,
    )

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    sample_file = tmp_path / "file.txt"
    sample_file.write_text("data")

    file_list_path = transfer.save(str(log_dir), [str(sample_file)])

    log_files = list(log_dir.glob("TransferLog_*.log"))
    assert log_files, "expected transfer log file to be created"
    assert os.path.isfile(file_list_path)

    with log_files[0].open() as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "Timestamp"
    assert any(file_list_path in row for row in rows)


def test_request_log_writes_file_list_and_log(tmp_path):
    config = DummyConfig()
    request_log = RequestLog(
        config=config,
        timestamp="20250101-020304",
        request_date="01/02/2025",
        requestor="Requester",
        computer_name="HOST",
        purpose="Testing",
        file_count=1,
        total_size=10,
    )

    file_list_dir = tmp_path / "requests"
    file_list_dir.mkdir()
    sample_file = tmp_path / "req.txt"
    sample_file.write_text("request data")

    file_list_path = request_log._save_file_list_with_progress(
        str(file_list_dir),
        [str(sample_file)],
        file_hashes={},
        progress_callback=None,
        is_canceled_callback=lambda: False,
    )

    assert os.path.isfile(file_list_path)

    request_csv = tmp_path / "RequestLog.csv"
    request_log._save_request_log(str(request_csv), "2025-01-02 02:03:04", file_list_path)

    with request_csv.open() as f:
        rows = list(csv.reader(f))
    assert rows[0][0] == "Timestamp"
    assert rows[1][2] == "Requester"
    assert file_list_path in rows[1]
