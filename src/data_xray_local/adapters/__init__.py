"""Local adapters. No adapter in this package performs network I/O."""

from data_xray_local.adapters.files import LocalFileExtractor, LocalFileSource

__all__ = ["LocalFileExtractor", "LocalFileSource"]
