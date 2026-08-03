from constants import (
    TRANSFER_LOG_HEADERS,
    FILE_LIST_HEADERS,
    REQUEST_LOG_HEADERS,
    REQUEST_FILE_LIST_HEADERS,
)


def test_constant_headers_present():
    assert len(TRANSFER_LOG_HEADERS) == 13
    assert len(FILE_LIST_HEADERS) == 5
    assert len(REQUEST_LOG_HEADERS) == 8
    assert len(REQUEST_FILE_LIST_HEADERS) == 5
