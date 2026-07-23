from __future__ import annotations

from data_xray_local.domain.models import DataCategory, Severity
from data_xray_local.domain.risk import (
    LocatedMatch,
    assign_duplicate_groups,
    build_heatmap,
    build_recommendations,
    severity_for_score,
)
from data_xray_local.domain.rules import DetectedMatch


def match(raw: str, category: DataCategory = DataCategory.EMAIL) -> DetectedMatch:
    from data_xray_local.domain.rules import comparison_digest, mask_value

    return DetectedMatch(
        rule_id="email-address",
        category=category,
        severity=Severity.MEDIUM,
        location="text · line 1, column 1",
        masked_fragment=mask_value(category, raw),
        remediation="Remove it.",
        comparison_digest=comparison_digest(category, raw),
        raw_value=raw,
    )


def test_duplicate_groups_require_separate_paths() -> None:
    located = [
        LocatedMatch("a.txt", match("a@example.com")),
        LocatedMatch("a.txt", match("a@example.com")),
        LocatedMatch("b.txt", match("a@example.com")),
        LocatedMatch("c.txt", match("c@example.com")),
    ]
    findings, duplicates = assign_duplicate_groups(located)

    assert len(duplicates) == 1
    assert duplicates[0].group_id == "dup-001"
    assert duplicates[0].paths == ("a.txt", "b.txt")
    assert sum(finding.duplicate_group == "dup-001" for finding in findings) == 3
    assert all(not hasattr(finding, "raw_value") for finding in findings)


def test_heatmap_orders_highest_risk_first() -> None:
    located = [
        LocatedMatch("low.txt", match("a@example.com")),
        LocatedMatch("high.txt", match("b@example.com")),
        LocatedMatch("high.txt", match("c@example.com")),
        LocatedMatch("high.txt", match("d@example.com")),
        LocatedMatch("high.txt", match("e@example.com")),
        LocatedMatch("high.txt", match("f@example.com")),
    ]
    findings, duplicates = assign_duplicate_groups(located)
    heatmap = build_heatmap(findings)
    recommendations = build_recommendations(findings, duplicates)

    assert heatmap[0].path == "high.txt"
    assert heatmap[0].risk_score > heatmap[1].risk_score
    assert recommendations[0].affected_files == 2


def test_severity_boundaries_are_stable() -> None:
    assert severity_for_score(0) == Severity.LOW
    assert severity_for_score(10) == Severity.MEDIUM
    assert severity_for_score(30) == Severity.HIGH
    assert severity_for_score(60) == Severity.CRITICAL
