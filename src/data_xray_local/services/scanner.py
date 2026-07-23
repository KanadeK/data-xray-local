"""Orchestrate local file discovery, extraction, detection, and aggregation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path

from data_xray_local.adapters.files import (
    FileAccessError,
    FileTooLargeError,
    LocalFileExtractor,
    LocalFileSource,
    UnsupportedFileError,
)
from data_xray_local.adapters.network import NoNetworkGuard
from data_xray_local.domain.models import (
    FileSummary,
    Finding,
    ScanReport,
    ScanSummary,
)
from data_xray_local.domain.risk import (
    LocatedMatch,
    assign_duplicate_groups,
    build_heatmap,
    build_recommendations,
    category_counts,
    score_findings,
)
from data_xray_local.domain.rules import DetectedMatch, Detector, comparison_digest, mask_value
from data_xray_local.version import __version__

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


class ScannerService:
    """Run a deterministic, local-only privacy exposure audit."""

    def __init__(
        self,
        *,
        source: LocalFileSource | None = None,
        extractor: LocalFileExtractor | None = None,
        detector: Detector | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._source = source or LocalFileSource()
        self._extractor = extractor or LocalFileExtractor()
        self._detector = detector or Detector()
        self._clock = clock

    def scan(self, root: Path, *, no_network: bool = True) -> ScanReport:
        root = root.expanduser()
        files = self._source.discover(root)
        located_matches: list[LocatedMatch] = []
        file_state: dict[str, tuple[str, int, str, str | None]] = {}
        guard = NoNetworkGuard() if no_network else nullcontext()

        with guard:
            for path in files:
                relative_path = self._source.relative_path(root, path)
                size_bytes = self._safe_size(path)
                try:
                    document = self._extractor.extract(path)
                    file_state[relative_path] = (
                        document.file_type,
                        size_bytes,
                        "scanned",
                        None,
                    )
                    for chunk in document.chunks:
                        for match in self._detector.detect(chunk.text, chunk.location):
                            located_matches.append(LocatedMatch(path=relative_path, match=match))
                    for signal in document.metadata_signals:
                        located_matches.append(
                            LocatedMatch(
                                path=relative_path,
                                match=DetectedMatch(
                                    rule_id=signal.rule_id,
                                    category=signal.category,
                                    severity=signal.severity,
                                    location=signal.location,
                                    masked_fragment=mask_value(signal.category, signal.value),
                                    remediation=signal.remediation,
                                    comparison_digest=comparison_digest(
                                        signal.category, signal.value
                                    ),
                                    raw_value=signal.value,
                                ),
                            )
                        )
                except (UnsupportedFileError, FileTooLargeError) as error:
                    file_state[relative_path] = (
                        path.suffix.casefold().removeprefix(".") or "unknown",
                        size_bytes,
                        "skipped",
                        str(error),
                    )
                except FileAccessError as error:
                    file_state[relative_path] = (
                        path.suffix.casefold().removeprefix(".") or "unknown",
                        size_bytes,
                        "error",
                        str(error),
                    )

        findings, duplicates = assign_duplicate_groups(located_matches)
        findings_by_path: dict[str, list[Finding]] = defaultdict(list)
        for finding in findings:
            findings_by_path[finding.path].append(finding)

        file_summaries: list[FileSummary] = []
        for relative, (file_type, size_bytes, status, note) in sorted(file_state.items()):
            per_file = findings_by_path[relative]
            file_summaries.append(
                FileSummary(
                    path=relative,
                    file_type=file_type,
                    size_bytes=size_bytes,
                    status=status,
                    risk_score=score_findings(per_file),
                    finding_count=len(per_file),
                    category_counts=category_counts(tuple(per_file)),
                    note=note,
                )
            )

        heatmap = build_heatmap(findings)
        recommendations = build_recommendations(findings, duplicates)
        warnings: list[str] = [
            "Heuristic results require human review; a clean scan is not proof of safe disclosure."
        ]
        if any(item.status == "skipped" for item in file_summaries):
            warnings.append(
                "Some files were skipped because their type or size is outside the MVP limit."
            )
        if any(item.status == "error" for item in file_summaries):
            warnings.append("Some files could not be read; review those paths manually.")

        summary = ScanSummary(
            files_discovered=len(files),
            files_scanned=sum(item.status == "scanned" for item in file_summaries),
            files_skipped=sum(item.status == "skipped" for item in file_summaries),
            files_with_errors=sum(item.status == "error" for item in file_summaries),
            findings=len(findings),
            high_risk_files=sum(item.risk_score >= 30 for item in file_summaries),
            duplicate_groups=len(duplicates),
            category_counts=category_counts(findings),
        )
        source_label = root.name or root.resolve().name or "scan-target"
        return ScanReport(
            product_version=__version__,
            generated_at=self._clock(),
            source_label=source_label,
            network_disabled=no_network,
            summary=summary,
            files=tuple(file_summaries),
            findings=findings,
            heatmap=heatmap,
            duplicate_exposures=duplicates,
            recommendations=recommendations,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _safe_size(path: Path) -> int:
        try:
            return path.stat().st_size
        except OSError:
            return 0
