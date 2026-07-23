from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from data_xray_local.cli import app

runner = CliRunner()


@pytest.mark.e2e
def test_cli_scan_generates_real_bundle(sample_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "report"
    result = runner.invoke(app, ["scan", str(sample_path), "--output", str(output)])

    assert result.exit_code == 0, result.output
    assert "masked finding(s)" in result.output
    assert (output / "data-xray-report.html").is_file()
    assert (output / "data-xray-report.json").is_file()


@pytest.mark.e2e
def test_cli_fail_on_returns_policy_exit_after_writing_report(
    sample_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "policy-report"
    result = runner.invoke(
        app,
        [
            "scan",
            str(sample_path),
            "--output",
            str(output),
            "--fail-on",
            "high",
        ],
    )

    assert result.exit_code == 10
    assert (output / "data-xray-report.json").is_file()


@pytest.mark.e2e
def test_cli_missing_target_returns_actionable_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["scan", str(tmp_path / "missing")])

    assert result.exit_code == 2
    assert "Scan failed: scan target does not exist" in result.output


@pytest.mark.e2e
def test_cli_demo_uses_explicit_sample(sample_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "demo"
    result = runner.invoke(
        app,
        ["demo", "--sample", str(sample_path), "--output", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert "Demo report:" in result.output
    assert (output / "data-xray-report.html").is_file()
