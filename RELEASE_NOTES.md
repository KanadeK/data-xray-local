# Data XRay Local v0.1.0

Data XRay Local is a read-only, local-first privacy exposure scanner for disclosure folders and
export packages. It identifies personal-data and credential shapes across text, CSV, JSON, modern
Office documents, and common image EXIF without uploading source files or serializing complete
matches.

## Highlights

- Deterministic CLI and loopback-only FastAPI interface.
- Masked JSON plus a self-contained offline HTML report.
- Relative-path heatmap, opaque cross-file repeat groups, and cleanup priorities.
- Synthetic CC0 demonstration data spanning CSV, JSON, text, DOCX, XLSX, and JPEG EXIF.
- Explicit no-network guard, bounded file handling, and fail-closed privacy regression tests.
- Reproducible wheel, source distribution, source/demo bundle, sample reports, and SHA-256 list.

## Verify the download

Download `SHA256SUMS.txt` with the release assets and compare the SHA-256 digest before use.

## Known boundaries

v0.1.0 does not alter source files and is not legal advice or compliance certification. It does
not yet inspect PDFs, archives, legacy binary Office files, video, audio, or OCR-only content.
