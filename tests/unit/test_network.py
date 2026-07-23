from __future__ import annotations

import socket

import pytest

from data_xray_local.adapters.network import NetworkDisabledError, NoNetworkGuard


def test_no_network_guard_blocks_dns() -> None:
    with NoNetworkGuard(), pytest.raises(NetworkDisabledError):
        socket.getaddrinfo("example.com", 443)


def test_no_network_guard_restores_socket_helpers() -> None:
    original = socket.getaddrinfo
    with NoNetworkGuard():
        assert socket.getaddrinfo is not original
    assert socket.getaddrinfo is original
