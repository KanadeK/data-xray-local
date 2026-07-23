"""Generate the repository's real offline demonstration report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_xray_local.reporting import write_report_bundle  # noqa: E402
from data_xray_local.services.scanner import ScannerService  # noqa: E402


def _verify_manifest(sample: Path) -> None:
    manifest = json.loads((sample / "MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("real_personal_data") is not False:
        raise RuntimeError("sample manifest must explicitly deny real personal data")
    if manifest.get("license") != "CC0-1.0":
        raise RuntimeError("sample fixture license is not CC0-1.0")


def main() -> int:
    sample = ROOT / "examples" / "synthetic_export"
    _verify_manifest(sample)
    report = ScannerService().scan(sample, no_network=True)
    output = ROOT / "reports" / "demo"
    json_path, html_path = write_report_bundle(report, output)
    print(
        f"Demo complete: {report.summary.files_scanned} scanned files, "
        f"{report.summary.findings} masked findings, "
        f"{report.summary.duplicate_groups} repeated exposure groups."
    )
    print(f"HTML: {html_path.relative_to(ROOT)}")
    print(f"JSON: {json_path.relative_to(ROOT)}")
    if not {
        "email",
        "phone",
        "postal_address",
        "government_id",
        "credential_or_token",
        "payment_card",
        "gps_location",
        "author_metadata",
    }.issubset({category.value for category in report.summary.category_counts}):
        raise RuntimeError("demo did not exercise every required detector category")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
