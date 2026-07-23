from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_xray_local.adapters.files import (
    FileAccessError,
    FileTooLargeError,
    LocalFileExtractor,
    LocalFileSource,
    UnsupportedFileError,
)
from data_xray_local.domain.models import DataCategory


def test_extract_text_csv_and_json(tmp_path: Path) -> None:
    text = tmp_path / "note.txt"
    csv_file = tmp_path / "contacts.csv"
    json_file = tmp_path / "profile.json"
    text.write_text("a@example.com", encoding="utf-8")
    csv_file.write_text("name,email\nA,a@example.com\n", encoding="utf-8")
    json_file.write_text(json.dumps({"person": {"email": "a@example.com"}}), encoding="utf-8")
    extractor = LocalFileExtractor()

    assert extractor.extract(text).chunks[0].location == "text"
    assert extractor.extract(csv_file).chunks[-1].location == "table · row 2, column 2"
    assert extractor.extract(json_file).chunks[0].location == "$.person.email"


def test_invalid_json_error_is_sanitized(tmp_path: Path) -> None:
    path = tmp_path / "private-profile.json"
    path.write_text('{"email": "secret@example.com",}', encoding="utf-8")

    with pytest.raises(FileAccessError) as captured:
        LocalFileExtractor().extract(path)

    assert str(path) not in str(captured.value)
    assert "secret@example.com" not in str(captured.value)
    assert str(captured.value) == "invalid JSON syntax"


def test_unsupported_and_oversized_files_are_explicit(tmp_path: Path) -> None:
    binary = tmp_path / "archive.bin"
    binary.write_bytes(b"data")
    large = tmp_path / "large.txt"
    large.write_text("x" * 11, encoding="utf-8")

    with pytest.raises(UnsupportedFileError):
        LocalFileExtractor().extract(binary)
    with pytest.raises(FileTooLargeError):
        LocalFileExtractor(max_file_size=10).extract(large)


def test_source_discovery_is_sorted_and_excludes_build_directories(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "old.txt").write_text("old", encoding="utf-8")

    names = [path.name for path in LocalFileSource().discover(tmp_path)]

    assert names == ["a.txt", "b.txt"]


def test_office_and_exif_metadata_are_extracted(sample_path: Path) -> None:
    extractor = LocalFileExtractor()
    xlsx = extractor.extract(sample_path / "contact-register.xlsx")
    docx = extractor.extract(sample_path / "disclosure-brief.docx")
    image = extractor.extract(sample_path / "field-photo.jpg")

    assert any(signal.category == DataCategory.AUTHOR_METADATA for signal in xlsx.metadata_signals)
    assert any(signal.category == DataCategory.AUTHOR_METADATA for signal in docx.metadata_signals)
    assert any(signal.category == DataCategory.GPS_LOCATION for signal in image.metadata_signals)
    assert any("EXIF" in chunk.location for chunk in image.chunks)
