"""Risk scoring, duplicate grouping, heatmap construction, and recommendations."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from data_xray_local.domain.models import (
    DataCategory,
    DuplicateExposure,
    Finding,
    HeatCell,
    Recommendation,
    Severity,
)
from data_xray_local.domain.rules import DetectedMatch

SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.LOW: 2,
    Severity.MEDIUM: 7,
    Severity.HIGH: 18,
    Severity.CRITICAL: 35,
}


@dataclass(frozen=True, slots=True)
class LocatedMatch:
    path: str
    match: DetectedMatch


def score_findings(findings: list[Finding] | tuple[Finding, ...]) -> int:
    unique_categories = len({finding.category for finding in findings})
    base = sum(SEVERITY_WEIGHT[finding.severity] for finding in findings)
    diversity_bonus = max(0, unique_categories - 1) * 4
    return min(100, base + diversity_bonus)


def severity_for_score(score: int) -> Severity:
    if score >= 60:
        return Severity.CRITICAL
    if score >= 30:
        return Severity.HIGH
    if score >= 10:
        return Severity.MEDIUM
    return Severity.LOW


def assign_duplicate_groups(
    located_matches: list[LocatedMatch],
) -> tuple[tuple[Finding, ...], tuple[DuplicateExposure, ...]]:
    """Convert ephemeral matches to safe findings and numbered duplicate groups."""

    grouped: dict[tuple[DataCategory, str], list[LocatedMatch]] = defaultdict(list)
    for item in located_matches:
        grouped[(item.match.category, item.match.comparison_digest)].append(item)

    duplicate_keys = sorted(
        (
            key
            for key, items in grouped.items()
            if len(items) >= 2 and len({item.path for item in items}) >= 2
        ),
        key=lambda key: (key[0].value, key[1]),
    )
    group_ids = {key: f"dup-{index:03d}" for index, key in enumerate(duplicate_keys, start=1)}

    findings: list[Finding] = []
    for item in located_matches:
        key = (item.match.category, item.match.comparison_digest)
        findings.append(
            Finding(
                category=item.match.category,
                severity=item.match.severity,
                path=item.path,
                location=item.match.location,
                masked_fragment=item.match.masked_fragment,
                rule_id=item.match.rule_id,
                remediation=item.match.remediation,
                duplicate_group=group_ids.get(key),
            )
        )

    duplicates: list[DuplicateExposure] = []
    for key in duplicate_keys:
        items = grouped[key]
        duplicates.append(
            DuplicateExposure(
                group_id=group_ids[key],
                category=key[0],
                count=len(items),
                paths=tuple(sorted({item.path for item in items})),
                masked_fragment=items[0].match.masked_fragment,
            )
        )

    findings.sort(key=lambda finding: (finding.path, finding.location, finding.rule_id))
    return tuple(findings), tuple(duplicates)


def apply_group_ids(
    findings: tuple[Finding, ...], duplicates: tuple[DuplicateExposure, ...]
) -> tuple[Finding, ...]:
    """Return findings unchanged when groups are already assigned.

    Kept as a small public pure function for callers that deserialize reports.
    """

    valid_ids = {group.group_id for group in duplicates}
    return tuple(
        finding.model_copy(update={"duplicate_group": None})
        if finding.duplicate_group not in valid_ids
        else finding
        for finding in findings
    )


def build_heatmap(findings: tuple[Finding, ...]) -> tuple[HeatCell, ...]:
    per_path: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        per_path[finding.path].append(finding)
    cells = [
        HeatCell(
            path=path,
            risk_score=score_findings(items),
            severity=severity_for_score(score_findings(items)),
            finding_count=len(items),
            categories=tuple(
                sorted({item.category for item in items}, key=lambda item: item.value)
            ),
        )
        for path, items in per_path.items()
    ]
    return tuple(sorted(cells, key=lambda cell: (-cell.risk_score, cell.path)))


RECOMMENDATION_TEXT: dict[DataCategory, tuple[str, str]] = {
    DataCategory.TOKEN: (
        "Rotate exposed credentials first",
        "Revoke each credential, verify recent use, then replace the source value with a clearly "
        "non-working synthetic marker.",
    ),
    DataCategory.GOVERNMENT_ID: (
        "Remove government identifiers",
        "Move originals to approved restricted storage and create a disclosure copy without the "
        "identifier.",
    ),
    DataCategory.PAYMENT_CARD: (
        "Escalate payment-data exposure",
        "Remove card data and follow the applicable payment incident and retention procedure.",
    ),
    DataCategory.GPS_LOCATION: (
        "Strip precise image locations",
        "Remove GPS EXIF before sharing and confirm that exported thumbnails do not retain it.",
    ),
    DataCategory.ADDRESS: (
        "Generalize street-level addresses",
        "Keep only the city or region required for the recipient's task.",
    ),
    DataCategory.EMAIL: (
        "Replace personal email addresses",
        "Use role aliases or synthetic addresses in examples and public export packages.",
    ),
    DataCategory.PHONE: (
        "Remove direct phone numbers",
        "Keep direct numbers only in the smallest access-controlled source set.",
    ),
    DataCategory.AUTHOR_METADATA: (
        "Clean document authorship metadata",
        "Clear creator, last-modified-by, and comment metadata before publishing.",
    ),
}


def build_recommendations(
    findings: tuple[Finding, ...], duplicates: tuple[DuplicateExposure, ...]
) -> tuple[Recommendation, ...]:
    category_paths: dict[DataCategory, set[str]] = defaultdict(set)
    category_severity: dict[DataCategory, Severity] = {}
    for finding in findings:
        category_paths[finding.category].add(finding.path)
        previous = category_severity.get(finding.category, Severity.LOW)
        if SEVERITY_WEIGHT[finding.severity] > SEVERITY_WEIGHT[previous]:
            category_severity[finding.category] = finding.severity

    recommendations = [
        Recommendation(
            priority=category_severity.get(category, Severity.MEDIUM),
            category=category,
            title=RECOMMENDATION_TEXT[category][0],
            action=RECOMMENDATION_TEXT[category][1],
            affected_files=len(paths),
        )
        for category, paths in category_paths.items()
    ]
    if duplicates:
        duplicated_paths = {path for group in duplicates for path in group.paths}
        recommendations.append(
            Recommendation(
                priority=Severity.HIGH,
                category=None,
                title="Break repeated exposure chains",
                action="Start with the canonical source, then remove or regenerate every duplicate "
                "copy listed in the exposure groups.",
                affected_files=len(duplicated_paths),
            )
        )

    recommendations.sort(
        key=lambda item: (
            -SEVERITY_WEIGHT[item.priority],
            -(item.affected_files),
            item.title,
        )
    )
    return tuple(recommendations)


def category_counts(findings: tuple[Finding, ...]) -> dict[DataCategory, int]:
    counts = Counter(finding.category for finding in findings)
    return {category: counts[category] for category in sorted(counts, key=lambda item: item.value)}
