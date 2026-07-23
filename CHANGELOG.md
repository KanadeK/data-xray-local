# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-28

### Added

- Offline scanning for text, CSV, JSON, Office Open XML content and metadata, and image EXIF.
- Masked detection for email, phone, postal address, government identifier, credentials,
  payment data, geolocation metadata, and author metadata.
- Cross-file duplicate exposure groups, per-file risk heatmap, and prioritized cleanup advice.
- Typer CLI, local FastAPI interface, sanitized JSON export, and self-contained HTML report.
- Deterministic synthetic export package and end-to-end privacy regression coverage.
- Reproducible build, release packaging, checksum generation, and GitHub Actions workflows.

### Fixed

- Avoid native `libmagic` discovery on Windows hosted runners and use the documented,
  deterministic `mimetypes` fallback when the native library is unavailable.
- Accept only the exact `v0.1.0` tag checkout, in addition to `main`, in the fail-closed
  release gate used by GitHub Actions.
- Normalize generated JSON to LF, make XLSX archive metadata byte-deterministic, and verify
  every synthetic manifest checksum before demo, Pages, or Release publication.

[0.1.0]: https://github.com/KanadeK/data-xray-local/releases/tag/v0.1.0
