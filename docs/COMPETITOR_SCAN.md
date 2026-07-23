# Public repository sample and differentiation

Scan date: **2026-07-23 (Asia/Shanghai)**  
Source: GitHub public repository search, repository metadata, and each selected repository README.
Stars and activity are a point-in-time observation and will change.

## Identity and name preflight

- The GitHub connector identified the authenticated user as `KanadeK` (numeric ID `121669563`).
- The original GitHub CLI credential was expired. An official Git Credential Manager browser flow
  replaced it, and an authenticated `gh api user` request then confirmed `KanadeK` (numeric ID
  `121669563`) before any commit or repository creation.
- Exact display-name search for `Data XRay Local`: **0 results**.
- Exact slug search for `data-xray-local`: no exact repository; one unrelated lung X-ray repository
  matched the separate words.
- Direct lookup of `KanadeK/data-xray-local`: **404 Not Found** before creation.

The name therefore remains **Data XRay Local** / `data-xray-local`.

## Queries sampled

1. `"Data XRay Local" in:name,description`
2. `data-xray-local in:name`
3. `PII scanner local files privacy`
4. `"sensitive data" scanner files`
5. `"PII detection" in:name,description`
6. `personal-data scanner in:name,description`
7. `"data loss prevention" file scanner in:name,description`
8. targeted repository/README checks for leading PII, secret, database, and metadata tools

## Most relevant repositories inspected

| Repository | Stars | Recent activity observed | Main capability | Overlap and boundary |
|---|---:|---|---|---|
| [wfps60412/Preupload-Guard](https://github.com/wfps60412/Preupload-Guard) | 2 | Updated 2026-06-28 | Offline file/folder/ZIP/Office scanner and sanitized-copy workflow | Highest overlap. It focuses on pre-upload sanitization and treats images as manual review; Data XRay Local stays read-only and adds EXIF GPS/authorship plus cross-file exposure groups. |
| [LokaalHub/filenthropist](https://github.com/LokaalHub/filenthropist) | 1 | Updated 2026-04-20 | Dutch PII labeling, local database/dashboard, AI-agent access gate, RoPA export | Strong local-first overlap, but model/download, Dutch governance, persistence, and agent authorization are different goals. |
| [davidgoh24/PDPA-Scanner](https://github.com/davidgoh24/PDPA-Scanner) | 0 | Updated 2025-08-23 | Offline SG-focused folder scan and HTML/CSV/JSON reports | Similar user flow; lacks cross-file duplicate mapping and image EXIF, and is jurisdiction-specific. |
| [jonberenguer/sensitive-data-scanner](https://github.com/jonberenguer/sensitive-data-scanner) | 1 | Updated 2026-05-08 | Cross-platform secret/PII binary with full and redacted reports | Similar detection/reporting, but intentionally creates a raw-value report; this project structurally cannot serialize raw values. |
| [Hirakhyzer/personal-data-privacy-risk-scanner](https://github.com/Hirakhyzer/personal-data-privacy-risk-scanner) | 0 | Updated 2026-07-22 | Synthetic privacy-risk research lab, recommendations, audit ledger | Shares risk/recommendation language; it is a research simulation rather than a general folder/export parser. |
| [cumakurt/filemeta](https://github.com/cumakurt/filemeta) | 3 | Updated 2026-05-11 | File/web metadata, Office/PDF analysis, HTML and sensitive-value export | Broad format overlap; includes web crawling and raw sensitive-data export, outside this project's no-network/report-minimization boundary. |
| [data-privacy-stack/presidio](https://github.com/data-privacy-stack/presidio) | 10.1k | Release 2026-07-22 | Extensible PII identification/anonymization SDK for text, images, and structured data | Far deeper detector engine. It is an SDK/service, not a zero-configuration folder exposure map with relative-path reporting. |
| [tokern/piicatcher](https://github.com/tokern/piicatcher) | 346 | Updated 2026-06-25; archived | PII discovery in databases/warehouses and data-catalog tagging | Overlaps on classification, but targets schemas, columns, plugins, and persistent catalogs rather than disclosure folders. |
| [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | 28,273 | Updated 2026-07-23 | High-performance secret detection in Git history, directories, and stdin | Excellent credential scanner; not intended for personal addresses, Office authorship, EXIF GPS, or cleanup heatmaps. |
| [exiftool/exiftool](https://github.com/exiftool/exiftool) | 4,890 | Updated 2026-07-23 | Comprehensive metadata reader/writer across many media types | Much broader metadata support; it exposes metadata but does not classify privacy risk or connect repeated exposure across files. |
| [sam247/openredaction](https://github.com/sam247/openredaction) | 97 | Updated 2026-07-23 | Local JavaScript PII library/redactor with a large rule catalog | Much broader rule catalog; it is a text library/redactor rather than a multi-format local evidence and path-audit product. |

## Overlap decision

`Preupload-Guard` is the closest repository, but after inspecting its README the effective MVP
overlap is below the stop threshold:

- common: offline folder scanning, text/Office inspection, PII and credentials, masked report;
- its center: prevent upload by sanitizing/copying/excluding source content;
- this project's center: explain **where personal identity leaks across formats and copies** while
  preserving provenance and never modifying the source;
- differentiators implemented here: common image EXIF GPS/authorship, strict no-raw report schema,
  opaque cross-file repeat groups, per-file privacy heatmap, and prioritized disclosure cleanup.

No code, rule catalog, design asset, or fixture was copied from the sampled repositories.

## Claim permitted in README

> An initial public GitHub repository sample found no active project with the same name and a
> highly isomorphic combination.

This is a bounded, dated sampling claim—not a statement of global uniqueness.
