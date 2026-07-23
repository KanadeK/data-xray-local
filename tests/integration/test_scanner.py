from __future__ import annotations

import socket
from pathlib import Path

import pytest

from data_xray_local.adapters.files import FileAccessError, LocalFileExtractor
from data_xray_local.adapters.network import NetworkDisabledError
from data_xray_local.domain.models import DataCategory
from data_xray_local.reporting import render_html_report, write_report_bundle
from data_xray_local.services.scanner import ScannerService

RAW_VALUES = (
    "avery.north@example.com",
    "+1 (202) 555-0147",
    "1847 Example Street",
    "899-12-3456",
    "990000199001010018",
    "AKIAIOSFODNN7EXAMPLE",
    "ghp_000000000000000000000000000000000000",
    "4111 1111 1111 1111",
)


@pytest.mark.integration
def test_sample_scan_exercises_every_required_category(
    sample_path: Path, fixed_scanner: ScannerService
) -> None:
    report = fixed_scanner.scan(sample_path, no_network=True)

    assert report.summary.files_discovered == 9
    assert report.summary.files_scanned == 9
    assert report.summary.files_skipped == 0
    assert report.summary.files_with_errors == 0
    assert report.summary.findings >= 20
    assert report.summary.duplicate_groups >= 3
    assert set(report.summary.category_counts) == set(DataCategory)
    assert report.generated_at.isoformat() == "2026-07-23T08:00:00+00:00"
    assert report.source_label == "synthetic_export"
    assert report.network_disabled is True


@pytest.mark.integration
def test_serialized_reports_never_contain_raw_values(
    sample_path: Path, fixed_scanner: ScannerService, tmp_path: Path
) -> None:
    report = fixed_scanner.scan(sample_path)
    json_path, html_path = write_report_bundle(report, tmp_path)
    serialized = json_path.read_text(encoding="utf-8") + html_path.read_text(encoding="utf-8")

    for raw in RAW_VALUES:
        assert raw not in serialized
    assert str(sample_path.resolve()) not in serialized
    assert "a•••@e•••.com" in serialized


@pytest.mark.integration
def test_invalid_and_unsupported_files_remain_visible(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text('{"email": }', encoding="utf-8")
    (tmp_path / "archive.bin").write_bytes(b"\x00\x01")

    report = ScannerService().scan(tmp_path)
    state = {item.path: item for item in report.files}

    assert state["broken.json"].status == "error"
    assert state["broken.json"].note == "invalid JSON syntax"
    assert state["archive.bin"].status == "skipped"
    assert report.summary.files_with_errors == 1
    assert report.summary.files_skipped == 1


@pytest.mark.integration
def test_permission_failure_is_reported_without_source_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = tmp_path / "restricted.txt"
    secret.write_text("avery.north@example.com", encoding="utf-8")
    extractor = LocalFileExtractor()

    def denied(_path: Path) -> None:
        raise FileAccessError("permission denied")

    monkeypatch.setattr(extractor, "extract", denied)
    report = ScannerService(extractor=extractor).scan(tmp_path)

    assert report.files[0].status == "error"
    assert report.files[0].note == "permission denied"
    assert "avery.north@example.com" not in report.model_dump_json()


@pytest.mark.integration
def test_no_network_flag_fails_closed_on_adapter_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "note.txt"
    path.write_text("safe", encoding="utf-8")
    extractor = LocalFileExtractor()

    def attempted_network(_path: Path) -> None:
        socket.getaddrinfo("example.com", 443)

    monkeypatch.setattr(extractor, "extract", attempted_network)
    with pytest.raises(NetworkDisabledError):
        ScannerService(extractor=extractor).scan(tmp_path, no_network=True)


@pytest.mark.integration
def test_html_renderer_escapes_path_content(tmp_path: Path, fixed_scanner: ScannerService) -> None:
    target = tmp_path / "folder"
    target.mkdir()
    (target / "x&script.txt").write_text("a@example.com", encoding="utf-8")
    report = fixed_scanner.scan(target)
    rendered = render_html_report(report)

    assert "x&amp;script.txt" in rendered
    assert "x&script.txt" not in rendered
    assert "Content-Security-Policy" in rendered


def test_missing_target_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ScannerService().scan(tmp_path / "missing")
