from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts.generate_sample_data import (
    FIXED_DOCUMENT_TIME_TEXT,
    FIXED_ZIP_TIMESTAMP,
    generate,
)
from scripts.sample_manifest import (
    SampleManifestError,
    file_sha256,
    verify_sample_manifest,
)

ROOT = Path(__file__).resolve().parents[2]


def test_committed_synthetic_manifest_matches_fixture_bytes() -> None:
    manifest = verify_sample_manifest(ROOT / "examples" / "synthetic_export")

    assert manifest["license"] == "CC0-1.0"
    assert manifest["real_personal_data"] is False


def test_sample_manifest_rejects_tampered_fixture(tmp_path: Path) -> None:
    sample = tmp_path / "sample"
    sample.mkdir()
    fixture = sample / "profile.json"
    fixture.write_text('{"synthetic": true}\n', encoding="utf-8", newline="\n")
    manifest = {
        "license": "CC0-1.0",
        "real_personal_data": False,
        "files": [{"path": fixture.name, "sha256": file_sha256(fixture)}],
    }
    (sample / "MANIFEST.json").write_text(
        json.dumps(manifest) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    fixture.write_text('{"synthetic": false}\n', encoding="utf-8", newline="\n")

    with pytest.raises(SampleManifestError, match="checksum mismatch"):
        verify_sample_manifest(sample)


def test_sample_generator_is_byte_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    generate(first, allowed_root=tmp_path)
    generate(second, allowed_root=tmp_path)

    first_manifest = verify_sample_manifest(first)
    second_manifest = verify_sample_manifest(second)
    first_hashes = {item["path"]: item["sha256"] for item in first_manifest["files"]}
    second_hashes = {item["path"]: item["sha256"] for item in second_manifest["files"]}
    assert first_hashes == second_hashes
    assert file_sha256(first / "MANIFEST.json") == file_sha256(second / "MANIFEST.json")

    with zipfile.ZipFile(first / "contact-register.xlsx") as archive:
        assert archive.infolist()
        assert all(item.date_time == FIXED_ZIP_TIMESTAMP for item in archive.infolist())
        core_properties = archive.read("docProps/core.xml").decode("utf-8")
        assert (
            f'<dcterms:modified xsi:type="dcterms:W3CDTF">'
            f"{FIXED_DOCUMENT_TIME_TEXT}</dcterms:modified>"
        ) in core_properties
