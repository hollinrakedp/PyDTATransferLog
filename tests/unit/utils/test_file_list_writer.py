import os
import csv
import types
from utils import file_list_writer


class DummyConfig:
    def get(self, *_args, **kwargs):
        return kwargs.get("fallback")


def test_save_file_list_writes_rows_and_uses_hashes(tmp_path, monkeypatch):
    captured_paths = []

    def fake_process(writer, display_path, normalized_hashes, level, container, hash_calc):
        captured_paths.append(display_path)
        writer.writerow([display_path, normalized_hashes.get(display_path, "") if normalized_hashes else ""])

    monkeypatch.setattr(file_list_writer.ArchiveProcessor, "process_file_with_archives", fake_process)

    f1 = tmp_path / "a.txt"
    f1.write_text("data", encoding="utf-8")
    hashes = {os.path.normpath(os.path.abspath(str(f1))): "hash1"}

    out = file_list_writer.save_file_list_with_progress(
        output_dir=str(tmp_path),
        files=[str(f1)],
        file_hashes=hashes,
        csv_headers=["Path", "Hash"],
        filename_template="{counter}.csv",
        template_data={},
        config=DummyConfig(),
        path_formatter=lambda p: p,
    )

    assert os.path.exists(out)
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == ["Path", "Hash"]
    assert rows[1][0] == str(f1)
    assert rows[1][1] == "hash1"
    assert captured_paths == [str(f1)]


def test_save_file_list_increments_counter(tmp_path, monkeypatch):
    # Pre-create 001.csv to force counter increment
    existing = tmp_path / "001.csv"
    existing.write_text("pre-existing", encoding="utf-8")

    def no_op(writer, display_path, normalized_hashes, level, container, hash_calc):
        writer.writerow([display_path])

    monkeypatch.setattr(file_list_writer.ArchiveProcessor, "process_file_with_archives", no_op)

    f1 = tmp_path / "b.txt"
    f1.write_text("data", encoding="utf-8")

    out = file_list_writer.save_file_list_with_progress(
        output_dir=str(tmp_path),
        files=[str(f1)],
        file_hashes=None,
        csv_headers=["Path"],
        filename_template="{counter}.csv",
        template_data={},
        config=DummyConfig(),
        path_formatter=lambda p: p,
    )

    assert out.endswith("002.csv")


def test_save_file_list_handles_cancel(tmp_path, monkeypatch):
    def fake_process(writer, display_path, normalized_hashes, level, container, hash_calc):
        writer.writerow([display_path])

    monkeypatch.setattr(file_list_writer.ArchiveProcessor, "process_file_with_archives", fake_process)

    f1 = tmp_path / "c.txt"
    f1.write_text("data", encoding="utf-8")

    out = file_list_writer.save_file_list_with_progress(
        output_dir=str(tmp_path),
        files=[str(f1)],
        file_hashes=None,
        csv_headers=["Path"],
        filename_template="{counter}.csv",
        template_data={},
        config=DummyConfig(),
        cancel_check=lambda: True,
    )

    assert out == ""
    assert not any(p.suffix == ".csv" for p in tmp_path.iterdir())


def test_save_file_list_cleans_on_error(tmp_path, monkeypatch):
    def boom(writer, display_path, normalized_hashes, level, container, hash_calc):
        raise RuntimeError("fail")

    monkeypatch.setattr(file_list_writer.ArchiveProcessor, "process_file_with_archives", boom)

    f1 = tmp_path / "d.txt"
    f1.write_text("data", encoding="utf-8")

    out = file_list_writer.save_file_list_with_progress(
        output_dir=str(tmp_path),
        files=[str(f1)],
        file_hashes=None,
        csv_headers=["Path"],
        filename_template="{counter}.csv",
        template_data={},
        config=DummyConfig(),
    )

    assert out == ""
    assert not any(p.suffix == ".csv" for p in tmp_path.iterdir())


def test_save_file_list_reports_progress(tmp_path, monkeypatch):
    def fake_process(writer, display_path, normalized_hashes, level, container, hash_calc):
        writer.writerow([display_path])

    monkeypatch.setattr(file_list_writer.ArchiveProcessor, "process_file_with_archives", fake_process)

    f1 = tmp_path / "e1.txt"
    f2 = tmp_path / "e2.txt"
    f1.write_text("data", encoding="utf-8")
    f2.write_text("more", encoding="utf-8")

    progresses = []

    class Progress:
        def emit(self, value: int):
            progresses.append(value)

    out = file_list_writer.save_file_list_with_progress(
        output_dir=str(tmp_path),
        files=[str(f1), str(f2)],
        file_hashes=None,
        csv_headers=["Path"],
        filename_template="{counter}.csv",
        template_data={},
        config=DummyConfig(),
        progress_callback=Progress(),
        path_formatter=lambda p: p,
    )

    assert out.endswith("001.csv")
    assert 50 in progresses or 100 in progresses


def test_save_file_list_uses_default_path_formatter_and_handles_bad_hash_map(tmp_path, monkeypatch):
    class BadMap(dict):
        def items(self):
            raise ValueError("boom")

    def fake_process(writer, display_path, normalized_hashes, level, container, hash_calc):
        writer.writerow([display_path, normalized_hashes])

    monkeypatch.setattr(file_list_writer.ArchiveProcessor, "process_file_with_archives", fake_process)

    f1 = tmp_path / "f.txt"
    f1.write_text("data", encoding="utf-8")

    out = file_list_writer.save_file_list_with_progress(
        output_dir=str(tmp_path),
        files=[str(f1)],
        file_hashes=BadMap(),
        csv_headers=["Path", "Hash"],
        filename_template="{counter}.csv",
        template_data={},
        config=DummyConfig(),
    )

    assert os.path.exists(out)
    with open(out, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert rows[1][0].endswith("f.txt")


def test_save_file_list_progress_callback_exception_is_swallowed(tmp_path, monkeypatch):
    def fake_process(writer, display_path, normalized_hashes, level, container, hash_calc):
        writer.writerow([display_path])

    monkeypatch.setattr(file_list_writer.ArchiveProcessor, "process_file_with_archives", fake_process)

    f1 = tmp_path / "g1.txt"
    f2 = tmp_path / "g2.txt"
    f1.write_text("data", encoding="utf-8")
    f2.write_text("more", encoding="utf-8")

    class BadProgress:
        def emit(self, _value):
            raise RuntimeError("no-ui")

    out = file_list_writer.save_file_list_with_progress(
        output_dir=str(tmp_path),
        files=[str(f1), str(f2)],
        file_hashes=None,
        csv_headers=["Path"],
        filename_template="{counter}.csv",
        template_data={},
        config=DummyConfig(),
        progress_callback=BadProgress(),
        path_formatter=None,
    )

    assert os.path.exists(out)
