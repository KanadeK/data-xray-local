# Privacy and security

## Security objective

The scanner should help a user find disclosure risk without turning its own report into another
copy of the sensitive data. Source files stay local and unchanged. The result is advisory evidence,
not approval to publish.

## Threat model

| Threat | v0.1.0 control | Residual risk |
|---|---|---|
| Report leaks a matched value | No serializable raw field; masks; leak regression tests | A mask can still be identifying in context |
| Absolute path exposes username | Only root-relative paths enter the report model | A relative filename itself can be sensitive |
| Same value appears in many copies | Ephemeral digest becomes opaque repeat group | Digest exists in process memory during scan |
| Parser processes hostile OOXML | Size bound, `defusedxml`, read-only ZIP access | Decompression cost and library defects remain possible |
| EXIF reveals a precise place | GPS is detected as high risk and fully hidden | Unsupported metadata containers may be missed |
| Tool unexpectedly calls a service | No online adapter; default DNS/socket helper guard | Loopback Web UI necessarily uses local HTTP |
| Scan follows an unexpected link | Symlink targets and symlinked directories are rejected | Windows reparse-point edge cases need continued review |
| Malicious name injects report markup | HTML escape plus restrictive report CSP | Browser/OS bugs are outside the application boundary |

## What is persisted

Reports may contain:

- source label (the selected file/folder basename);
- relative file path, type, size, and scan status;
- finding category, severity, rule identifier, location, and masked fragment;
- counts, heat scores, opaque duplicate labels, and cleanup advice;
- generated time and product/schema versions.

Reports do not contain:

- complete detector matches;
- source snippets;
- absolute source or target paths;
- equality digests;
- file contents, cookies, access tokens, or telemetry.

The output folder path appears in CLI console output for user convenience, but is not part of the
report payload.

## `--no-network`

There is no HTTP, GitHub, cloud, model-download, telemetry, or update adapter in the product.
`--no-network` is the default and wraps extraction/detection in a guard that blocks DNS resolution
and `socket.create_connection`. A regression test injects an adapter network attempt and verifies
that it fails closed.

The FastAPI interface binds to `127.0.0.1` by default. Browser requests to that loopback process are
local network transport, not outbound disclosure. Binding to a LAN address is allowed only with a
visible CLI warning and should be avoided for sensitive review.

## Safe operating guidance

1. Scan a copy or read-only source when provenance matters.
2. Keep reports in an access-controlled folder; masked context can still be sensitive.
3. Review skipped/error files manually.
4. Revoke exposed credentials before deleting or editing the source.
5. Create a separate disclosure copy and scan it again.
6. Do not treat a zero-finding report as a compliance decision.

## Known format boundaries

v0.1.0 does not parse PDF, OCR, legacy DOC/XLS/PPT, nested archives, encrypted files, email mailbox
formats, database files, audio/video metadata, thumbnails embedded outside supported EXIF, or
steganographic content. It decodes UTF-8/UTF-16 text but does not guess arbitrary legacy encodings.
Rules have false positives and false negatives and are not jurisdiction-complete.

These are visible product limits, not deferred implementation stubs. Planned optional PDF/OCR work
is listed in the README roadmap and must preserve the same local and masked-report contracts.

## Dependency and release controls

- Runtime and development dependencies are exact-pinned; CI installs `requirements-dev.lock`.
- Office XML uses `defusedxml`; native MIME detection has a deterministic `mimetypes` fallback.
- CI runs Ruff, formatting, strict mypy, 80% total coverage, build, sample generation, and packaging.
- Security CI runs `pip-audit` and the repository's deterministic credential-shape scanner.
- Release packaging installs the built wheel into a clean temporary target before success.
- The release gate checks a clean `main`, version consistency, authorship, synthetic secret
  allow-list, empty implementation markers, artifacts, and tests.

