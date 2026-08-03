from PySide6.QtCore import QDate
from models.review_model import ReviewModel


class DummyConfig:
    def get(self, *_args, **_kwargs):
        return None


def _sample_entries():
    return [
        ["20251201-120000", "12/01/2025", "Alice", "PC1", "Flash", "M1", "L2H", "Src", "Dst", "3", "10", "path1"],
        ["20251202-120000", "12/02/2025", "Bob", "PC2", "Flash", "M2", "L2H", "Src", "Dst", "2", "5", "path2"],
        ["20251130-120000", "11/30/2025", "Carl", "PC3", "HDD", "M3", "H2L", "A", "B", "5", "20", "path3"],
    ]


def test_filter_date_range():
    model = ReviewModel(DummyConfig())
    entries = _sample_entries()
    start = QDate(2025, 12, 1)
    end = QDate(2025, 12, 31)
    filtered = model.filter_entries(entries, start_date=start, end_date=end)
    assert len(filtered) == 2
    assert all(e[1].startswith("12/") for e in filtered)


def test_search_matches_any_field():
    model = ReviewModel(DummyConfig())
    entries = _sample_entries()
    results = model.filter_entries(entries, search_text="carl")
    assert len(results) == 1
    assert results[0][2] == "Carl"


def test_sort_entries_full_dataset():
    model = ReviewModel(DummyConfig())
    entries = _sample_entries()
    model.sort_entries(entries, column=1, reverse=False)
    assert entries[0][1] == "11/30/2025"
    model.sort_entries(entries, column=10, reverse=True)
    assert entries[0][10] == "20"


def test_paginate_entries_respects_page_size():
    model = ReviewModel(DummyConfig())
    entries = _sample_entries()
    page = model.paginate_entries(entries, page=1, page_size=2)
    assert len(page) == 2
    page2 = model.paginate_entries(entries, page=2, page_size=2)
    assert len(page2) == 1
