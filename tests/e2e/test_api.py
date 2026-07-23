from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from data_xray_local.api import app

client = TestClient(app)


@pytest.mark.e2e
def test_web_interface_has_keyboard_and_accessibility_basics() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert '<html lang="en">' in response.text
    assert 'name="viewport"' in response.text
    assert 'href="#scan-form"' in response.text
    assert 'for="target"' in response.text
    assert 'type="submit"' in response.text
    assert 'aria-live="polite"' in response.text
    assert "@media(max-width:760px)" in response.text
    assert "@media(prefers-reduced-motion:reduce)" in response.text


@pytest.mark.e2e
def test_api_scan_returns_sanitized_report_and_writes_artifacts(
    sample_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "api-report"
    response = client.post(
        "/api/scan",
        json={"target": str(sample_path), "output": str(output), "no_network": True},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["report"]["network_disabled"] is True
    assert payload["report"]["summary"]["findings"] >= 20
    assert payload["artifacts"] == {
        "json": "data-xray-report.json",
        "html": "data-xray-report.html",
    }
    assert "avery.north@example.com" not in response.text
    assert (output / "data-xray-report.html").is_file()


@pytest.mark.e2e
def test_api_rejects_missing_target(tmp_path: Path) -> None:
    response = client.post(
        "/api/scan",
        json={"target": str(tmp_path / "missing"), "output": str(tmp_path / "out")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "scan target does not exist"


def test_health_is_local_only() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["network"] == "local-only"
    assert response.headers["x-frame-options"] == "DENY"
