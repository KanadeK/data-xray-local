"""Deterministic repository credential-shape gate with explicit synthetic allow-list."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "generic-secret": re.compile(
        r"(?i)\b(?:api[_-]?key|password|secret)\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{20,}"
    ),
}
ALLOWED_PREFIXES = (
    "examples/synthetic_export/",
    "scripts/generate_sample_data.py",
    "tests/",
)


def main() -> int:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git executable is required")
    tracked = subprocess.run(
        [git, "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
    ).stdout.splitlines()
    violations: list[str] = []
    for relative in tracked:
        path = ROOT / relative
        if not path.is_file() or path.suffix.casefold() in {".jpg", ".jpeg", ".xlsx", ".docx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in PATTERNS.items():
            if pattern.search(text) and not relative.startswith(ALLOWED_PREFIXES):
                violations.append(f"{relative}: {name}")
    if violations:
        raise RuntimeError(
            "credential-like content outside synthetic fixtures:\n" + "\n".join(violations)
        )
    print(f"Secret scan passed across {len(tracked)} tracked files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
