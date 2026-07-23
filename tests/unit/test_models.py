from __future__ import annotations

import pytest
from pydantic import ValidationError

from data_xray_local.domain.models import DataCategory, Finding, Severity


def valid_finding(**updates: object) -> Finding:
    values: dict[str, object] = {
        "category": DataCategory.EMAIL,
        "severity": Severity.MEDIUM,
        "path": "contacts.csv",
        "location": "row 2",
        "masked_fragment": "a•••@e•••.com",
        "rule_id": "email-address",
        "remediation": "Remove it.",
    }
    values.update(updates)
    return Finding(**values)


@pytest.mark.parametrize("path", ["C:/Users/example/file.txt", "../secret.txt", "/etc/passwd"])
def test_finding_rejects_absolute_or_traversal_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        valid_finding(path=path)


def test_finding_rejects_unknown_raw_value_field() -> None:
    with pytest.raises(ValidationError):
        valid_finding(raw_value="avery.north@example.com")


def test_finding_accepts_safe_relative_path_and_is_frozen() -> None:
    finding = valid_finding(path="nested\\contacts.csv")
    assert finding.path == "nested/contacts.csv"
    with pytest.raises(ValidationError):
        finding.path = "other.txt"  # type: ignore[misc]
