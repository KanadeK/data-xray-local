from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from data_xray_local.services.scanner import ScannerService

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "synthetic_export"
FIXED_TIME = datetime(2026, 7, 23, 8, 0, tzinfo=UTC)


@pytest.fixture
def sample_path() -> Path:
    return SAMPLE


@pytest.fixture
def fixed_scanner() -> ScannerService:
    return ScannerService(clock=lambda: FIXED_TIME)
