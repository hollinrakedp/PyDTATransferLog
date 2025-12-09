import os
from utils import cli_utils


def test_resolve_output_folder_relative_cli(tmp_path):
    user_cwd = tmp_path
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    out = cli_utils.resolve_output_folder("logs", "./default", str(user_cwd), str(app_dir))
    assert os.path.commonpath([out, str(user_cwd / "logs")]) == str(user_cwd / "logs")


def test_resolve_output_folder_absolute_cli(tmp_path):
    user_cwd = tmp_path
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    target = tmp_path / "abs_logs"
    out = cli_utils.resolve_output_folder(str(target), "./default", str(user_cwd), str(app_dir))
    assert out == os.path.abspath(str(target))


def test_resolve_output_folder_config_default(tmp_path):
    user_cwd = tmp_path
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    default = "./default_logs"
    out = cli_utils.resolve_output_folder(None, default, str(user_cwd), str(app_dir))
    assert os.path.commonpath([out, str(app_dir / "default_logs")]) == str(app_dir / "default_logs")


def test_collect_files_includes_and_warns(tmp_path):
    base = tmp_path
    good = base / "good.txt"
    good.write_text("data", encoding="utf-8")
    missing = base / "missing.txt"
    messages = []

    def capture(msg: str):
        messages.append(msg)

    files = cli_utils.collect_files([str(good)], [str(missing)], str(base), print_fn=capture)
    assert os.path.abspath(str(good)) in files
    assert any("Warning: Directory not found" in m for m in messages)


def test_collect_files_recurses(tmp_path):
    base = tmp_path
    subdir = base / "folder"
    subdir.mkdir()
    nested = subdir / "nested.txt"
    nested.write_text("x", encoding="utf-8")

    files = cli_utils.collect_files([], [str(subdir)], str(base))
    assert os.path.abspath(str(nested)) in files


def test_collect_files_warns_missing_file(tmp_path):
    messages = []

    def capture(msg: str):
        messages.append(msg)

    files = cli_utils.collect_files([str(tmp_path / "missing.txt")], [], str(tmp_path), print_fn=capture)
    assert files == []
    assert any("File not found" in msg for msg in messages)


def test_compute_hashes_success_and_progress(tmp_path, monkeypatch):
    f1 = tmp_path / "a.txt"
    f1.write_text("data", encoding="utf-8")
    f2 = tmp_path / "b.txt"
    f2.write_text("more", encoding="utf-8")

    calls = []
    monkeypatch.setattr(cli_utils, "calculate_file_hash", lambda path, algorithm='sha256': f"HASH-{os.path.basename(path)}")

    hashes = cli_utils.compute_hashes([str(f1), str(f2)], progress_step=1, print_fn=lambda msg: calls.append(msg))

    assert hashes[str(f1)] == "HASH-a.txt"
    assert hashes[str(f2)] == "HASH-b.txt"
    assert calls[-1] == "Processed 2/2 files"


def test_compute_hashes_captures_errors(tmp_path, monkeypatch):
    f1 = tmp_path / "a.txt"
    f1.write_text("data", encoding="utf-8")

    def boom(_path, algorithm='sha256'):
        raise RuntimeError("fail")

    monkeypatch.setattr(cli_utils, "calculate_file_hash", boom)

    hashes = cli_utils.compute_hashes([str(f1)], progress_step=1, print_fn=lambda msg: None)

    assert hashes[str(f1)].startswith("ERROR: fail")
