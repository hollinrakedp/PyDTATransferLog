import os
from utils import file_utils


class DummyConfig:
    def __init__(self, local_network=""):
        self.local_network = local_network

    def get(self, section, key, fallback=None):
        if key == "LocalNetwork":
            return self.local_network or fallback
        if key == "DateFormat":
            return "yyyyMMdd"
        if key == "TimeFormat":
            return "HHmmss"
        return fallback


def test_format_display_path_normalizes(tmp_path):
    p = tmp_path / "nested" / "file.txt"
    p.parent.mkdir()
    p.write_text("x", encoding="utf-8")
    normalized = file_utils.format_display_path(str(p))
    assert os.path.normpath(normalized) == normalized
    assert normalized.endswith("file.txt")


def test_sanitize_filename_replaces_invalid():
    name = "bad:name?.txt"
    sanitized = file_utils.sanitize_filename(name)
    assert ':' not in sanitized and '?' not in sanitized and '"' not in sanitized


def test_format_filename_counter_and_tokens(tmp_path):
    config = DummyConfig(local_network="DestNet")
    template = "{date}_{time}_{username}_{direction}_{counter}.csv"
    data = {"source": "SrcNet", "destination": "DestNet"}
    result = file_utils.format_filename(template, data=data, config=config, counter=7)
    assert result.endswith("007.csv")
    assert "Incoming" in result or "Outgoing" in result or "Unknown" in result


def test_format_filename_custom_format_specifiers():
    template = "{date:yyyy-MM-dd}_{time:HH-mm-ss}.log"
    result = file_utils.format_filename(template)
    assert len(result.split("_")) == 2
    assert result.endswith(".log")
