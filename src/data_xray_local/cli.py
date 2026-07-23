"""Typer command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from data_xray_local.domain.models import Severity
from data_xray_local.reporting import write_report_bundle
from data_xray_local.services.scanner import ScannerService
from data_xray_local.version import __version__

app = typer.Typer(
    name="data-xray",
    help="Scan a local folder for personal-data exposure without uploading its contents.",
    no_args_is_help=True,
)


def _exit_for_threshold(report_highest: Severity | None, threshold: str) -> None:
    if threshold == "none" or report_highest is None:
        return
    order = {
        Severity.LOW: 0,
        Severity.MEDIUM: 1,
        Severity.HIGH: 2,
        Severity.CRITICAL: 3,
    }
    selected = Severity(threshold)
    if order[report_highest] >= order[selected]:
        raise typer.Exit(code=10)


@app.command()
def scan(
    target: Annotated[
        Path,
        typer.Argument(
            exists=False,
            file_okay=True,
            dir_okay=True,
            readable=True,
            resolve_path=False,
            help="Local file or folder to inspect.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for sanitized JSON and HTML reports."),
    ] = Path("reports"),
    no_network: Annotated[
        bool,
        typer.Option(
            "--no-network/--allow-network",
            help="Fail closed on accidental DNS/socket use while scanning.",
        ),
    ] = True,
    fail_on: Annotated[
        str,
        typer.Option(
            "--fail-on",
            help="Exit 10 when this severity is present: none, low, medium, high, critical.",
        ),
    ] = "none",
) -> None:
    """Scan TARGET and produce a real local report bundle."""

    if fail_on not in {"none", "low", "medium", "high", "critical"}:
        raise typer.BadParameter("choose one of: none, low, medium, high, critical")
    try:
        report = ScannerService().scan(target, no_network=no_network)
    except (FileNotFoundError, PermissionError, OSError, RuntimeError, ValueError) as error:
        typer.echo(f"Scan failed: {error}", err=True)
        raise typer.Exit(code=2) from error

    json_path, html_path = write_report_bundle(report, output)
    typer.echo(
        f"Scanned {report.summary.files_scanned}/{report.summary.files_discovered} files; "
        f"{report.summary.findings} masked finding(s), "
        f"{report.summary.duplicate_groups} repeated exposure group(s)."
    )
    typer.echo(f"HTML: {html_path}")
    typer.echo(f"JSON: {json_path}")
    highest = report.heatmap[0].severity if report.heatmap else None
    _exit_for_threshold(highest, fail_on)


@app.command()
def demo(
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Directory for the generated demonstration."),
    ] = Path("reports/demo"),
    sample: Annotated[
        Path,
        typer.Option("--sample", help="Path to the bundled deterministic sample export."),
    ] = Path("examples/synthetic_export"),
) -> None:
    """Scan the repository's fictional sample export."""

    if not sample.exists():
        typer.echo(
            "Sample export not found. Run this command from the source repository "
            "or pass --sample explicitly.",
            err=True,
        )
        raise typer.Exit(code=2)
    report = ScannerService().scan(sample, no_network=True)
    _, html_path = write_report_bundle(report, output)
    typer.echo(f"Demo report: {html_path}")
    typer.echo(
        f"Detected {report.summary.findings} masked findings across "
        f"{report.summary.files_scanned} files."
    )


@app.command()
def serve(
    host: Annotated[str, typer.Option(help="Bind address; loopback is safest.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(min=1, max=65535)] = 8765,
) -> None:
    """Run the local FastAPI review interface."""

    import uvicorn

    if host not in {"127.0.0.1", "localhost", "::1"}:
        typer.echo(
            "Warning: non-loopback binding can expose the local review UI to your network.",
            err=True,
        )
    uvicorn.run("data_xray_local.api:app", host=host, port=port, log_level="info")


@app.command()
def version() -> None:
    """Print the installed version."""

    typer.echo(__version__)


if __name__ == "__main__":
    app()
