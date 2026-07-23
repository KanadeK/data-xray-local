# Contributing

Thank you for helping improve Data XRay Local.

## Ground rules

- Never submit real personal data, credentials, tokens, or proprietary documents.
- Use synthetic fixtures with reserved domains, test phone ranges, and clearly fictional names.
- Keep the domain layer independent from FastAPI, Typer, the filesystem, and the network.
- Findings persisted by the product may contain only relative paths, counts, categories, and
  masked fragments. Raw matches belong only in short-lived process memory.
- Every defect fix needs a regression test. Do not weaken a privacy assertion to make CI pass.

## Development

```bash
python -m pip install -e ".[dev]"
python scripts/verify.py
python scripts/demo.py
```

Run `python scripts/verify.py --fast` while iterating, then the full command before opening a
pull request. Format with `python -m ruff format .`.

## Pull requests

Keep changes focused and explain the privacy impact. Include the commands you ran, note any new
file formats or detectors, and update both READMEs when user-facing behavior changes. By
participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

