import csv
import io
import os
import tarfile
import zipfile
import gzip
from utils.archive_utils import ArchiveProcessor


def test_process_zip_includes_nested_files(tmp_path):
    zip_path = tmp_path / "sample.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("inner.txt", "hello world")

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

    ArchiveProcessor.process_file_with_archives(
        writer,
        str(zip_path),
        {str(zip_path): "HASH"},
        level=0,
    )

    rows = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert rows[0][2] == str(zip_path)
    assert rows[0][4] == "HASH"
    assert any(row[2] == "inner.txt" for row in rows)


def test_process_tar_handles_members(tmp_path):
    tar_path = tmp_path / "sample.tar"
    inner_file = tmp_path / "inner.txt"
    inner_file.write_text("tar content")

    with tarfile.open(tar_path, "w") as tf:
        tf.add(inner_file, arcname="nested/inner.txt")

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

    ArchiveProcessor.process_file_with_archives(
        writer,
        str(tar_path),
        file_hashes={},
        level=0,
    )

    rows = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert any(row[2] == "nested/inner.txt" for row in rows)
    assert rows[0][2] == str(tar_path)


def test_process_gz_reports_extracted_file(tmp_path):
    gz_path = tmp_path / "file.txt.gz"
    content = b"gzip data"
    with gzip.open(gz_path, "wb") as gz_file:
        gz_file.write(content)

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

    ArchiveProcessor.process_file_with_archives(
        writer,
        str(gz_path),
        file_hashes={},
        level=0,
    )

    rows = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert rows[0][2] == str(gz_path)
    assert any(row[2].endswith("file.txt") for row in rows)
    assert any(row[3] == str(len(content)) for row in rows)


def test_process_file_with_archives_missing_file_writes_error():
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

    ArchiveProcessor.process_file_with_archives(writer, "nonexistent.zip", {}, level=0)

    rows = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert rows[0][3] == "ERROR"
    assert rows[0][4].startswith("ERROR:")


def test_process_zip_with_nested_tar_and_hash(tmp_path):
    # Build a tar archive in memory
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w:gz") as tf:
        info = tarfile.TarInfo(name="inner.txt")
        data = b"nested tar content"
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    tar_bytes.seek(0)

    # Embed the tar into a zip file
    zip_path = tmp_path / "nested.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("archive.tar.gz", tar_bytes.read())

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

    def fake_hash(payload: bytes) -> str:
        return f"HASH-{len(payload)}"

    ArchiveProcessor.process_file_with_archives(
        writer,
        str(zip_path),
        file_hashes={},
        level=0,
        hash_calculator=fake_hash,
    )

    rows = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert any(row[2] == "archive.tar.gz" for row in rows)
    assert any(row[2] == "inner.txt" for row in rows)
    assert any(row[4].startswith("HASH-") for row in rows)


def test_process_tar_with_nested_zip_fileobj(tmp_path):
    # Create a zip archive in memory
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("nested.txt", "hello")
    zip_bytes.seek(0)

    # Add the in-memory zip into a tar archive on disk
    tar_path = tmp_path / "container.tar"
    with tarfile.open(tar_path, "w") as tf:
        info = tarfile.TarInfo(name="inner.zip")
        info.size = len(zip_bytes.getvalue())
        tf.addfile(info, io.BytesIO(zip_bytes.getvalue()))

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

    ArchiveProcessor.process_file_with_archives(
        writer,
        str(tar_path),
        file_hashes={},
        level=0,
    )

    rows = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert any(row[2] == "inner.zip" for row in rows)
    assert any(row[2] == "nested.txt" for row in rows)


def test_process_gz_file_like_with_hash():
    gz_bytes = io.BytesIO()
    with gzip.GzipFile(fileobj=gz_bytes, mode="wb") as gz:
        gz.write(b"content")
    gz_bytes.seek(0)

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_ALL)

    ArchiveProcessor._process_gz_file(
        writer,
        gz_bytes,
        level=1,
        file_hashes={},
        container_name="sample.gz",
        hash_calculator=lambda data: f"HASH-{len(data)}",
    )

    rows = list(csv.reader(io.StringIO(buffer.getvalue())))
    assert rows[0][1] == "sample.gz"
    assert rows[0][2] == "sample"
    assert rows[0][4].startswith("HASH-")
