"""Cross-platform quality gate used locally and in CI."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run lint, formatting, types, and tests but skip the distribution build.",
    )
    args = parser.parse_args()

    run([sys.executable, "-m", "ruff", "check", "."])
    run([sys.executable, "-m", "ruff", "format", "--check", "."])
    run([sys.executable, "-m", "mypy", "src"])
    with tempfile.TemporaryDirectory(prefix=".pytest-run-", dir=ROOT) as temporary:
        run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                f"--basetemp={Path(temporary) / 'base'}",
                "--cov=src",
                "--cov-report=term-missing",
                "--cov-fail-under=80",
            ]
        )
    if not args.fast:
        run([sys.executable, "-m", "build"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
