# v0.1.0 release checklist

## Source and privacy

- [ ] Supported formats match both READMEs and tests.
- [ ] Every report model rejects unknown fields and absolute/traversal paths.
- [ ] Synthetic manifest says `real_personal_data: false` and `license: CC0-1.0`.
- [ ] Raw fixture values are absent from generated JSON and HTML.
- [ ] Unsupported, oversized, damaged, and unreadable files are visible.
- [ ] `--no-network` regression injects a network attempt and fails closed.
- [ ] `git grep` finds no empty implementation marker outside an explicit roadmap.
- [ ] `python scripts/secret_scan.py` passes.

## Unified local gates

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=80
python -m build
python scripts/demo.py
python scripts/package_release.py
```

Equivalent task gates:

```bash
make verify
make demo
make package
make release-check
```

On Windows without `make`, use `scripts/verify.ps1`, `scripts/demo.ps1`,
`scripts/package_release.ps1`, and `scripts/release_check.ps1`.

## Artifact checks

- [ ] Wheel and sdist exist.
- [ ] `data-xray-local-0.1.0-source-demo-any.zip` contains launchers and synthetic export.
- [ ] Sanitized HTML and JSON sample reports exist.
- [ ] Wheel installs with `--no-deps` into a clean temporary target and imports as v0.1.0.
- [ ] Every asset except `SHA256SUMS.txt` has one matching checksum entry.
- [ ] Extracted ZIP contains no `.env`, cache, database, report source, or build temporary file.

## Author and repository

```bash
gh auth status
gh api user --jq '{login,id,email}'
git log --format='%h %an <%ae> | %cn <%ce> %s'
git shortlog -sne HEAD
git log --format='%B' | rg -i 'Co-authored-by'
git status --short
```

- [ ] `gh` login is exactly the intended account.
- [ ] Git author and committer are `KanadeK` with the account email or GitHub noreply email.
- [ ] No `Co-authored-by` trailer and no other contributor.
- [ ] Public repository default branch is `main`.
- [ ] Description and topics are set; Homepage waits for successful Pages deployment.

## Online gates

- [ ] Main CI, compatibility, security, and Pages runs are green.
- [ ] Annotated `v0.1.0` tag points to the intended `main` commit.
- [ ] Release workflow reruns verification, builds assets, and publishes a non-draft release.
- [ ] Online asset names, sizes, and SHA-256 values match downloaded bytes.
- [ ] GitHub contributors page contains only the authenticated owner for v0.1.0 history.
- [ ] Pages serves only the synthetic sample report.

Do not mark the release complete while any item above is red or unknown.

