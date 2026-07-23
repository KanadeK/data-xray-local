"""FastAPI wrapper around the same offline scanner used by the CLI."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from data_xray_local.reporting import write_report_bundle
from data_xray_local.services.scanner import ScannerService
from data_xray_local.version import __version__


class ScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target: str = Field(min_length=1, max_length=4096)
    output: str = Field(default="reports/web", min_length=1, max_length=4096)
    no_network: bool = True


class ScanResponse(BaseModel):
    report: dict[str, Any]
    artifacts: dict[str, str]


app = FastAPI(
    title="Data XRay Local",
    version=__version__,
    description="Loopback API for local personal-data exposure audits.",
    docs_url=None,
    redoc_url=None,
)


@app.middleware("http")
async def add_security_headers(request: Any, call_next: Any) -> Response:
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", include_in_schema=False)
def index() -> Response:
    content = files("data_xray_local").joinpath("web/index.html").read_text(encoding="utf-8")
    return Response(content=content, media_type="text/html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__, "network": "local-only"}


@app.post("/api/scan", response_model=ScanResponse)
def scan_local(payload: ScanRequest) -> ScanResponse:
    try:
        report = ScannerService().scan(Path(payload.target), no_network=payload.no_network)
        json_path, html_path = write_report_bundle(report, Path(payload.output))
    except (FileNotFoundError, PermissionError, OSError, RuntimeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return ScanResponse(
        report=report.model_dump(mode="json"),
        artifacts={"json": json_path.name, "html": html_path.name},
    )
