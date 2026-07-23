"""Measure the core scanner against a deterministic local corpus."""

from __future__ import annotations

import json
import os
import platform
import shutil
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_xray_local.services.scanner import ScannerService  # noqa: E402

SOURCE = ROOT / "examples" / "synthetic_export"
WORK = ROOT / ".benchmark-tmp"
OUTPUT = ROOT / "reports" / "benchmark.json"
COPIES = 50
RUNS = 5


def _guarded_prepare() -> Path:
    resolved = WORK.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name != ".benchmark-tmp":
        raise RuntimeError("benchmark path escaped repository")
    if WORK.exists():
        shutil.rmtree(WORK)
    corpus = WORK / "corpus"
    corpus.mkdir(parents=True)
    for index in range(COPIES):
        shutil.copytree(SOURCE, corpus / f"export-{index:03d}")
    return corpus


def main() -> int:
    corpus = _guarded_prepare()
    scanner = ScannerService()
    scanner.scan(corpus, no_network=True)
    durations: list[float] = []
    final_report = None
    for _ in range(RUNS):
        started = time.perf_counter()
        final_report = scanner.scan(corpus, no_network=True)
        durations.append(time.perf_counter() - started)
    assert final_report is not None
    files = [path for path in corpus.rglob("*") if path.is_file()]
    payload = {
        "platform": platform.platform(),
        "processor": os.environ.get("PROCESSOR_IDENTIFIER") or platform.processor() or "unknown",
        "python": platform.python_version(),
        "copies": COPIES,
        "files": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "runs": RUNS,
        "median_seconds": round(statistics.median(durations), 4),
        "min_seconds": round(min(durations), 4),
        "max_seconds": round(max(durations), 4),
        "files_per_second_median": round(len(files) / statistics.median(durations), 1),
        "findings": final_report.summary.findings,
        "duplicate_groups": final_report.summary.duplicate_groups,
        "network_disabled": final_report.network_disabled,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.rmtree(WORK)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
