"""Transparent, deterministic privacy detection rules."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from data_xray_local.domain.models import DataCategory, Severity

Validator = Callable[[str], bool]


@dataclass(frozen=True, slots=True)
class DetectionRule:
    rule_id: str
    category: DataCategory
    severity: Severity
    pattern: re.Pattern[str]
    remediation: str
    validator: Validator | None = None


@dataclass(frozen=True, slots=True)
class DetectedMatch:
    """Ephemeral match.

    ``comparison_digest`` exists only long enough to build duplicate groups. ``raw_value`` is
    never stored; it is returned to the caller solely so privacy tests can assert the lifecycle.
    """

    rule_id: str
    category: DataCategory
    severity: Severity
    location: str
    masked_fragment: str
    remediation: str
    comparison_digest: str
    raw_value: str


EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]{1,64}@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,24}(?![\w.-])")
PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d(). -]{7,}\d)(?!\w)")
EN_ADDRESS = re.compile(
    r"(?i)(?<!\w)\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,5}\s+"
    r"(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)"
    r"(?:\s*,?\s*(?:Apt|Suite|Unit)\s*[A-Za-z0-9-]+)?"
)
ZH_ADDRESS = re.compile(
    r"(?:[\u4e00-\u9fff]{2,12}(?:省|自治区))?"
    r"[\u4e00-\u9fff]{2,12}市"
    r"[\u4e00-\u9fff]{1,12}(?:区|县)"
    r"[\u4e00-\u9fff0-9]{1,24}(?:路|街|巷|弄)"
    r"\d{1,6}号(?:\d{1,4}(?:室|单元))?"
)
CN_ID = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])"
    r"(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"
)
US_SSN = re.compile(r"(?<!\d)(?!000|666|9\d\d)\d{3}-(?!00)\d{2}-(?!0000)\d{4}(?!\d)")
AWS_KEY = re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")
GITHUB_TOKEN = re.compile(r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,255}(?![A-Za-z0-9])")
JWT = re.compile(
    r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,}\."
    r"[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}(?![A-Za-z0-9_-])"
)
GENERIC_SECRET = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\b"
    r"\s*[:=]\s*[\"']?([A-Za-z0-9_./+=-]{12,})[\"']?"
)
PAYMENT_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


def _valid_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 10 <= len(digits) <= 15 and len(set(digits)) >= 4


def _valid_luhn(value: str) -> bool:
    digits = [int(character) for character in value if character.isdigit()]
    if not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


RULES: tuple[DetectionRule, ...] = (
    DetectionRule(
        "email-address",
        DataCategory.EMAIL,
        Severity.MEDIUM,
        EMAIL,
        "Remove the address, replace it with a role alias, or keep the file in a restricted set.",
    ),
    DetectionRule(
        "phone-number",
        DataCategory.PHONE,
        Severity.MEDIUM,
        PHONE,
        "Remove or generalize the number unless direct contact is required.",
        _valid_phone,
    ),
    DetectionRule(
        "postal-address-en",
        DataCategory.ADDRESS,
        Severity.HIGH,
        EN_ADDRESS,
        "Remove street-level detail or retain only the region needed for the task.",
    ),
    DetectionRule(
        "postal-address-zh",
        DataCategory.ADDRESS,
        Severity.HIGH,
        ZH_ADDRESS,
        "删除门牌级地址，或仅保留完成任务所需的城市/区域信息。",
    ),
    DetectionRule(
        "government-id-cn",
        DataCategory.GOVERNMENT_ID,
        Severity.CRITICAL,
        CN_ID,
        "Remove the identifier and rotate any workflow that used it as a secret.",
    ),
    DetectionRule(
        "government-id-us",
        DataCategory.GOVERNMENT_ID,
        Severity.CRITICAL,
        US_SSN,
        "Remove the identifier and restrict the original document to an approved system.",
    ),
    DetectionRule(
        "aws-access-key",
        DataCategory.TOKEN,
        Severity.CRITICAL,
        AWS_KEY,
        "Revoke and rotate the key before sharing; removing the file alone is insufficient.",
    ),
    DetectionRule(
        "github-token",
        DataCategory.TOKEN,
        Severity.CRITICAL,
        GITHUB_TOKEN,
        "Revoke and rotate the token before sharing; review its recent use.",
    ),
    DetectionRule(
        "jwt-token",
        DataCategory.TOKEN,
        Severity.HIGH,
        JWT,
        "Invalidate the token and replace it with a documented synthetic value.",
    ),
    DetectionRule(
        "assigned-secret",
        DataCategory.TOKEN,
        Severity.HIGH,
        GENERIC_SECRET,
        "Move the credential to a secret store and replace the sample with a non-working marker.",
    ),
    DetectionRule(
        "payment-card",
        DataCategory.PAYMENT_CARD,
        Severity.CRITICAL,
        PAYMENT_CARD,
        "Remove the card number and follow the applicable payment-data incident procedure.",
        _valid_luhn,
    ),
)


def _normalized(category: DataCategory, value: str) -> str:
    if category in {
        DataCategory.PHONE,
        DataCategory.GOVERNMENT_ID,
        DataCategory.PAYMENT_CARD,
    }:
        return re.sub(r"\W", "", value).casefold()
    return re.sub(r"\s+", " ", value.strip()).casefold()


def comparison_digest(category: DataCategory, value: str) -> str:
    """Return an in-memory equality key without exposing the original value."""

    payload = f"{category.value}\0{_normalized(category, value)}".encode()
    return hashlib.sha256(payload).hexdigest()


def _masked_text(value: str, keep_start: int = 2, keep_end: int = 2) -> str:
    compact = value.strip()
    if len(compact) <= keep_start + keep_end:
        return "•" * len(compact)
    masked_length = min(12, len(compact) - keep_start - keep_end)
    return f"{compact[:keep_start]}{'•' * masked_length}{compact[-keep_end:]}"


def mask_value(category: DataCategory, value: str) -> str:
    """Create a useful fragment that never contains the full match."""

    compact = value.strip()
    if category == DataCategory.EMAIL and "@" in compact:
        local, domain = compact.rsplit("@", 1)
        domain_name, separator, suffix = domain.rpartition(".")
        local_mask = f"{local[:1]}•••" if local else "•••"
        domain_mask = f"{domain_name[:1]}•••" if domain_name else "•••"
        return f"{local_mask}@{domain_mask}{separator}{suffix}"
    if category == DataCategory.PHONE:
        digits = re.sub(r"\D", "", compact)
        return f"•••-•••-{digits[-4:]}" if len(digits) >= 4 else "••••"
    if category == DataCategory.ADDRESS:
        return f"{compact[:3]}…[street detail hidden]"
    if category == DataCategory.GOVERNMENT_ID:
        return _masked_text(compact, 2, 2)
    if category == DataCategory.TOKEN:
        candidate = compact.split("=", 1)[-1].strip("\"' ") if "=" in compact else compact
        return _masked_text(candidate, 4, 4)
    if category == DataCategory.PAYMENT_CARD:
        digits = re.sub(r"\D", "", compact)
        return f"•••• •••• •••• {digits[-4:]}"
    if category == DataCategory.GPS_LOCATION:
        return "[precise location hidden]"
    return _masked_text(compact, 1, 1)


def _line_and_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    previous_newline = text.rfind("\n", 0, offset)
    column = offset + 1 if previous_newline == -1 else offset - previous_newline
    return line, column


class Detector:
    """Apply the transparent rule set to a text chunk."""

    def __init__(self, rules: Iterable[DetectionRule] = RULES) -> None:
        self._rules = tuple(rules)

    def detect(self, text: str, location_prefix: str = "text") -> tuple[DetectedMatch, ...]:
        matches: list[DetectedMatch] = []
        claimed_spans: set[tuple[int, int, DataCategory]] = set()
        for rule in self._rules:
            for regex_match in rule.pattern.finditer(text):
                raw = (
                    regex_match.group(1)
                    if rule.rule_id == "assigned-secret" and regex_match.lastindex
                    else regex_match.group(0)
                )
                if rule.validator is not None and not rule.validator(raw):
                    continue
                span = (*regex_match.span(), rule.category)
                if span in claimed_spans:
                    continue
                claimed_spans.add(span)
                line, column = _line_and_column(text, regex_match.start())
                matches.append(
                    DetectedMatch(
                        rule_id=rule.rule_id,
                        category=rule.category,
                        severity=rule.severity,
                        location=f"{location_prefix} · line {line}, column {column}",
                        masked_fragment=mask_value(rule.category, raw),
                        remediation=rule.remediation,
                        comparison_digest=comparison_digest(rule.category, raw),
                        raw_value=raw,
                    )
                )
        return tuple(sorted(matches, key=lambda item: (item.location, item.rule_id)))
