from utils.cli_utils import format_timestamp


def test_format_timestamp_valid():
    ts = "20251207-153045"
    assert format_timestamp(ts) == "2025-12-07 15:30:45"


def test_format_timestamp_invalid_returns_input():
    ts = "bad"
    assert format_timestamp(ts) == ts


def test_format_timestamp_non_string_pass_through():
    ts = 12345
    assert format_timestamp(ts) == ts
