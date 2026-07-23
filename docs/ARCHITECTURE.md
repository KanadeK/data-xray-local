# Architecture

## Design constraints

Data XRay Local is a read-only, local-first review aid. The core must be testable without a UI,
network, filesystem mutation, current wall clock, or external service. Serializable output must
have no place to store a complete sensitive match.

## Components

```text
┌──────────────────────────────────────────────────────────────────────┐
│ User entry points                                                    │
│ Typer CLI            Loopback FastAPI + accessible HTML interface    │
└───────────┬──────────────────────────────┬───────────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           ▼
                 ScannerService (use case)
                           │
           ┌───────────────┼──────────────────┐
           ▼               ▼                  ▼
   LocalFileSource   LocalFileExtractor   NoNetworkGuard
   sorted walking    text/table/OOXML     DNS/socket fail-closed
                     EXIF chunks
           └───────────────┬──────────────────┘
                           ▼
                    Detector (domain)
           transparent regex + validators + masking
                           │
             ephemeral raw match + equality digest
                           │
                           ▼
       duplicate grouping / scoring / recommendations (domain)
                           │
                raw value and digest discarded
                           │
                           ▼
                     ScanReport model
       relative path + category + count + masked fragment only
                           │
                 ┌─────────┴──────────┐
                 ▼                    ▼
          sanitized JSON      standalone HTML report
```

## Package map

| Path | Responsibility |
|---|---|
| `domain/models.py` | Frozen, strict Pydantic report schema |
| `domain/rules.py` | Pure detection, validation, masks, ephemeral equality digest |
| `domain/risk.py` | Pure grouping, scoring, heatmap, cleanup ordering |
| `adapters/files.py` | Bounded local discovery and format-specific extraction |
| `adapters/network.py` | Explicit DNS/socket guard for `--no-network` |
| `services/scanner.py` | Use-case orchestration and injected clock |
| `reporting.py` | Escaped JSON and self-contained HTML renderers |
| `cli.py` | Typer commands and policy exit codes |
| `api.py`, `web/index.html` | Loopback API and keyboard-usable local interface |

The domain package does not import FastAPI, Typer, Pillow, openpyxl, `pathlib`, or socket APIs.
Adapters may depend on external libraries, but they return neutral chunks and metadata signals.

## Data lifecycle

1. `LocalFileSource` discovers regular files in deterministic order. It does not follow symlinks
   and excludes tool/build directories by default.
2. `LocalFileExtractor` reads a bounded file and emits text chunks labeled with a cell, JSON path,
   Office part, or EXIF tag. It never creates a source copy.
3. `Detector` creates an ephemeral `DetectedMatch`. This is the only object with `raw_value`; it is
   not a Pydantic model and has no serializer.
4. A SHA-256 comparison digest groups equal normalized values during the current scan. It is never
   placed in `ScanReport`.
5. Aggregation converts each ephemeral match to `Finding`, replaces digest links with sequential
   `dup-NNN` identifiers, and drops ephemeral objects after the call.
6. JSON and HTML writers accept only `ScanReport`.

## Failure semantics

- Missing target: the use case raises `FileNotFoundError`; CLI returns `2`, API returns `400`.
- Unsupported type or safety-size limit: file remains in the report as `skipped`.
- Parser, encoding, or permission failure: file remains as `error` with a fixed safe reason.
- Policy threshold: reports are written, then CLI returns `10`.
- Accidental network call under `--no-network`: `NetworkDisabledError` aborts the scan.

Skipped and failed files are never counted as safe.

## Extending a format

Add extraction in `LocalFileExtractor`, return `ContentChunk` and optional `MetadataSignal`, then
add:

1. a real synthetic fixture;
2. success and damaged-input tests;
3. a privacy serialization test;
4. size/performance evidence;
5. both README support tables and the security boundary.

An adapter may not return a report model or bypass the detector/aggregation path.

