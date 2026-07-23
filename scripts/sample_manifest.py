"""Validate the synthetic sample manifest against the exact fixture bytes."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class SampleManifestError(RuntimeError):
    """Raised when the public synthetic fixture manifest is inconsistent."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sample_manifest(sample: Path) -> dict[str, object]:
    """Fail closed when the manifest or any declared fixture byte differs."""

    manifest_path = sample / "MANIFEST.json"
    if not manifest_path.is_file():
        raise SampleManifestError("sample manifest is missing")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SampleManifestError("sample manifest is unreadable") from error
    if not isinstance(payload, dict):
        raise SampleManifestError("sample manifest root must be an object")
    manifest: dict[str, object] = payload
    if manifest.get("real_personal_data") is not False:
        raise SampleManifestError("sample manifest must explicitly deny real personal data")
    if manifest.get("license") != "CC0-1.0":
        raise SampleManifestError("sample fixture license is not CC0-1.0")

    records = manifest.get("files")
    if not isinstance(records, list):
        raise SampleManifestError("sample manifest files must be a list")
    declared: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            raise SampleManifestError("sample manifest file entry must be an object")
        name = record.get("path")
        expected = record.get("sha256")
        if (
            not isinstance(name, str)
            or not name
            or "/" in name
            or "\\" in name
            or Path(name).name != name
        ):
            raise SampleManifestError(f"unsafe sample manifest path: {name!r}")
        if not isinstance(expected, str) or SHA256_PATTERN.fullmatch(expected) is None:
            raise SampleManifestError(f"invalid SHA-256 for sample fixture: {name}")
        if name in declared:
            raise SampleManifestError(f"duplicate sample manifest path: {name}")
        declared.append(name)
        fixture = sample / name
        if not fixture.is_file() or fixture.is_symlink():
            raise SampleManifestError(f"sample fixture is missing or unsafe: {name}")
        actual = file_sha256(fixture)
        if actual != expected:
            raise SampleManifestError(
                f"sample fixture checksum mismatch: {name} expected {expected}, got {actual}"
            )

    actual_files = sorted(
        path.name for path in sample.iterdir() if path.is_file() and path.name != "MANIFEST.json"
    )
    if sorted(declared) != actual_files:
        raise SampleManifestError(
            "sample manifest file set mismatch: "
            f"declared={sorted(declared)!r}, actual={actual_files!r}"
        )
    return manifest
