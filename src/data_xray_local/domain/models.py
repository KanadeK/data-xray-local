"""Serializable report models.

The models intentionally have no field for an unmasked match. Raw detector values are
short-lived inputs to aggregation and cannot be serialized into a report by accident.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Base model that rejects silently ignored data."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class DataCategory(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "postal_address"
    GOVERNMENT_ID = "government_id"
    TOKEN = "credential_or_token"
    PAYMENT_CARD = "payment_card"
    GPS_LOCATION = "gps_location"
    AUTHOR_METADATA = "author_metadata"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Finding(StrictModel):
    """A privacy-safe detector result."""

    category: DataCategory
    severity: Severity
    path: str
    location: str = Field(max_length=160)
    masked_fragment: str = Field(min_length=1, max_length=96)
    rule_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    remediation: str = Field(max_length=240)
    duplicate_group: str | None = Field(default=None, pattern=r"^dup-\d{3}$")

    @field_validator("path")
    @classmethod
    def path_must_be_relative(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(normalized)
        if (
            posix_path.is_absolute()
            or windows_path.is_absolute()
            or ".." in posix_path.parts
            or ":" in normalized
        ):
            raise ValueError("report paths must be relative and traversal-free")
        return normalized


class FileSummary(StrictModel):
    path: str
    file_type: str
    size_bytes: int = Field(ge=0)
    status: str = Field(pattern=r"^(scanned|skipped|error)$")
    risk_score: int = Field(ge=0, le=100)
    finding_count: int = Field(ge=0)
    category_counts: dict[DataCategory, int]
    note: str | None = Field(default=None, max_length=240)

    @field_validator("path")
    @classmethod
    def path_must_be_relative(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(normalized)
        if (
            posix_path.is_absolute()
            or windows_path.is_absolute()
            or ".." in posix_path.parts
            or ":" in normalized
        ):
            raise ValueError("report paths must be relative and traversal-free")
        return normalized


class HeatCell(StrictModel):
    path: str
    risk_score: int = Field(ge=0, le=100)
    severity: Severity
    finding_count: int = Field(ge=0)
    categories: tuple[DataCategory, ...]


class DuplicateExposure(StrictModel):
    group_id: str = Field(pattern=r"^dup-\d{3}$")
    category: DataCategory
    count: int = Field(ge=2)
    paths: tuple[str, ...] = Field(min_length=2)
    masked_fragment: str = Field(min_length=1, max_length=96)


class Recommendation(StrictModel):
    priority: Severity
    category: DataCategory | None
    title: str = Field(max_length=120)
    action: str = Field(max_length=360)
    affected_files: int = Field(ge=1)


class ScanSummary(StrictModel):
    files_discovered: int = Field(ge=0)
    files_scanned: int = Field(ge=0)
    files_skipped: int = Field(ge=0)
    files_with_errors: int = Field(ge=0)
    findings: int = Field(ge=0)
    high_risk_files: int = Field(ge=0)
    duplicate_groups: int = Field(ge=0)
    category_counts: dict[DataCategory, int]


class ScanReport(StrictModel):
    schema_version: str = "1.0"
    product_version: str
    generated_at: datetime
    source_label: str = Field(min_length=1, max_length=200)
    network_disabled: bool
    summary: ScanSummary
    files: tuple[FileSummary, ...]
    findings: tuple[Finding, ...]
    heatmap: tuple[HeatCell, ...]
    duplicate_exposures: tuple[DuplicateExposure, ...]
    recommendations: tuple[Recommendation, ...]
    warnings: tuple[str, ...] = ()
