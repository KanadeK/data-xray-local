"""Fail-closed release gate for source, identity, tests, and artifacts."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0"
EXPECTED_AUTHOR = "KanadeK"
EMPTY_MARKER_WORDS = (
    "TO" + "DO",
    "FIX" + "ME",
    "Not" + "Implemented",
    "place" + "holder",
    "coming" + " soon",
    "lorem" + " ipsum",
)
EMPTY_MARKERS = re.compile(
    r"\b(?:" + "|".join(re.escape(marker) for marker in EMPTY_MARKER_WORDS) + r")\b",
    re.IGNORECASE,
)


def capture(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    return completed.stdout


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def tracked_files() -> list[Path]:
    return [ROOT / line for line in capture(["git", "ls-files"]).splitlines() if line]


def check_markers() -> None:
    violations: list[str] = []
    for path in tracked_files():
        if path.resolve() == Path(__file__).resolve():
            continue
        if not path.is_file() or path.suffix.casefold() in {".jpg", ".jpeg", ".xlsx", ".docx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.casefold() in {".yml", ".yaml"}:
            text = re.sub(r"(?m)^\s*placeholder\s*:.*$", "", text)
        if path.suffix.casefold() in {".htm", ".html"}:
            text = re.sub(r"(?mi)^\s*placeholder\s*=.*$", "", text)
        if EMPTY_MARKERS.search(text):
            violations.append(path.relative_to(ROOT).as_posix())
    check(not violations, f"empty implementation markers found in: {', '.join(violations)}")


def check_versions() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version_module = (ROOT / "src/data_xray_local/version.py").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    check(f'version = "{VERSION}"' in pyproject, "pyproject version mismatch")
    check(f'__version__ = "{VERSION}"' in version_module, "module version mismatch")
    check(f"## [{VERSION}]" in changelog, "CHANGELOG release entry missing")


def check_identity() -> None:
    log = capture(["git", "log", "--format=%an|%ae|%cn|%ce|%B"])
    check(log.strip() != "", "repository has no commits")
    for record in capture(["git", "log", "--format=%an|%ae|%cn|%ce"]).splitlines():
        author, _author_email, committer, _committer_email = record.split("|", 3)
        check(author == EXPECTED_AUTHOR, f"unexpected author: {author}")
        check(committer == EXPECTED_AUTHOR, f"unexpected committer: {committer}")
    check("Co-authored-by:" not in log, "Co-authored-by trailer is forbidden")


def check_synthetic_secrets_only() -> None:
    secret_pattern = re.compile(r"(?:AKIA|ASIA)[A-Z0-9]{16}|gh[pousr]_[A-Za-z0-9]{36,}")
    allowed_roots = ("examples/synthetic_export/", "scripts/generate_sample_data.py", "tests/")
    violations: list[str] = []
    for path in tracked_files():
        if not path.is_file() or path.suffix.casefold() in {".jpg", ".jpeg", ".xlsx", ".docx"}:
            continue
        relative = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if secret_pattern.search(text) and not relative.startswith(allowed_roots):
            violations.append(relative)
    check(not violations, f"credential-like value outside synthetic fixtures: {violations}")


def main() -> int:
    check(capture(["git", "status", "--porcelain"]).strip() == "", "worktree is not clean")
    check(capture(["git", "branch", "--show-current"]).strip() == "main", "release must be on main")
    check_versions()
    check_markers()
    check_identity()
    check_synthetic_secrets_only()
    release_dir = ROOT / "dist-release"
    check((release_dir / "SHA256SUMS.txt").is_file(), "release checksums are missing")
    check(any(release_dir.glob("*.whl")), "release wheel is missing")
    check(any(release_dir.glob("*.tar.gz")), "release sdist is missing")
    check(any(release_dir.glob("*sample-report-any.html")), "sample HTML report is missing")
    subprocess.run([sys.executable, "scripts/verify.py", "--fast"], cwd=ROOT, check=True)
    print("Release check passed: source, tests, artifacts, privacy, and author identity.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
