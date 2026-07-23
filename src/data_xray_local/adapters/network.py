"""Enforce the CLI's explicit no-network contract."""

from __future__ import annotations

import socket
from types import TracebackType
from typing import Any
from unittest.mock import patch


class NetworkDisabledError(RuntimeError):
    """Raised if code attempts name resolution or an outbound connection."""


def _blocked(*_args: Any, **_kwargs: Any) -> None:
    raise NetworkDisabledError("network access is disabled for this scan")


class NoNetworkGuard:
    """Process-local guard used around scan execution.

    The product has no online adapter. This guard additionally makes accidental DNS lookups and
    common socket connection helpers fail closed while a scan is running.
    """

    def __init__(self) -> None:
        self._patchers = (
            patch.object(socket, "create_connection", _blocked),
            patch.object(socket, "getaddrinfo", _blocked),
        )

    def __enter__(self) -> NoNetworkGuard:
        for patcher in self._patchers:
            patcher.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        for patcher in reversed(self._patchers):
            patcher.stop()
