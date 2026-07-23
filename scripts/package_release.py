"""Assemble reproducible v0.1.0 release assets and validate the wheel."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUTPUT = ROOT / "dist-release"
VERSION = "0.1.0"
SLUG = "data-xray-local"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _guarded_clean_output() -> None:
    resolved = OUTPUT.resolve()
    if resolved.parent != ROOT.resolve() or resolved.name != "dist-release":
        raise RuntimeError("refusing to clean unexpected release path")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()


def _copy_builds() -> list[Path]:
    builds = sorted(DIST.glob("*"))
    if not any(path.suffix == ".whl" for path in builds) or not any(
        path.name.endswith(".tar.gz") for path in builds
    ):
        raise RuntimeError("wheel and sdist must exist in dist; run python -m build first")
    copied: list[Path] = []
    for path in builds:
        destination = OUTPUT / path.name
        shutil.copy2(path, destination)
        copied.append(destination)
    return copied


def _source_bundle() -> Path:
    destination = OUTPUT / f"{SLUG}-{VERSION}-source-demo-any.zip"
    include_roots = [
        "examples/synthetic_export",
        "scripts/run_web.ps1",
        "scripts/run_web.sh",
        "README.md",
        "README.zh-CN.md",
        "LICENSE",
    ]
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in include_roots:
            path = ROOT / relative
            if path.is_dir():
                for candidate in sorted(path.rglob("*")):
                    if candidate.is_file():
                        archive.write(candidate, candidate.relative_to(ROOT).as_posix())
            else:
                archive.write(path, path.relative_to(ROOT).as_posix())
    return destination


def _smoke_wheel(wheel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="data-xray-wheel-") as temporary:
        target = Path(temporary) / "site"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-deps",
                "--target",
                str(target),
                str(wheel),
            ],
            check=True,
            cwd=temporary,
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(target)
        subprocess.run(
            [
                sys.executable,
                "-c",
                "import data_xray_local; assert data_xray_local.__version__ == '0.1.0'",
            ],
            check=True,
            cwd=temporary,
            env=environment,
        )


def main() -> int:
    _guarded_clean_output()
    assets = _copy_builds()
    demo_html = ROOT / "reports" / "demo" / "data-xray-report.html"
    demo_json = ROOT / "reports" / "demo" / "data-xray-report.json"
    if not demo_html.exists() or not demo_json.exists():
        raise RuntimeError("demo artifacts missing; run python scripts/demo.py first")
    html_asset = OUTPUT / f"{SLUG}-{VERSION}-sample-report-any.html"
    json_asset = OUTPUT / f"{SLUG}-{VERSION}-sample-report-any.json"
    shutil.copy2(demo_html, html_asset)
    shutil.copy2(demo_json, json_asset)
    assets.extend((html_asset, json_asset, _source_bundle()))

    wheel = next(path for path in assets if path.suffix == ".whl")
    _smoke_wheel(wheel)
    checksum_path = OUTPUT / "SHA256SUMS.txt"
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in sorted(assets)),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Packaged {len(assets)} assets in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
