from types import SimpleNamespace
from unittest.mock import patch
import subprocess

from beacon.monitor import NetworkMonitor


def test_is_non_public_ip():
    assert NetworkMonitor.is_non_public_ip("127.0.0.1") is True
    assert NetworkMonitor.is_non_public_ip("192.168.1.1") is True
    assert NetworkMonitor.is_non_public_ip("10.0.0.5") is True
    assert NetworkMonitor.is_non_public_ip("172.16.0.1") is True
    assert NetworkMonitor.is_non_public_ip("::1") is True
    assert NetworkMonitor.is_non_public_ip("fe80::1") is True
    assert NetworkMonitor.is_non_public_ip("0.0.0.0") is True
    assert NetworkMonitor.is_non_public_ip("invalid-ip") is True
    assert NetworkMonitor.is_non_public_ip("140.82.112.26") is False


def test_roast_level_classification():
    monitor = NetworkMonitor(trusted_processes={"Chrome.EXE"})

    assert monitor.get_roast_level("unknown_malware.exe", 443, "ESTABLISHED") == "BURNT"
    assert monitor.get_roast_level("cHrOmE.ExE", 8080, "ESTABLISHED") == "CRISPY"
    assert monitor.get_roast_level("chrome.exe", 443, "ESTABLISHED") == "SIZZLING"
    assert monitor.get_roast_level("chrome.exe", 443, "CLOSE_WAIT") == "RAW"
    monitor.shutdown()


def test_dns_timeout_falls_back_to_ip_and_clears_pending():
    monitor = NetworkMonitor(trusted_processes=set())
    ip = "140.82.112.26"
    monitor._pending_lookups.add(ip)

    with patch(
        "beacon.monitor.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="python", timeout=3),
    ):
        monitor._resolve_worker(ip)

    assert monitor._dns_cache[ip] == ip
    assert ip not in monitor._pending_lookups
    monitor.shutdown()


@patch("beacon.monitor.psutil.Process")
@patch("beacon.monitor.psutil.net_connections")
def test_scan_filters_and_groups_sockets(mock_net_conns, mock_process):
    mock_process.return_value.name.return_value = "chrome.exe"

    # Simulate 2 identical external sockets, 1 TIME_WAIT, and 1 local router socket
    mock_net_conns.return_value = [
        SimpleNamespace(
            pid=1234,
            laddr=SimpleNamespace(ip="192.168.0.10", port=50001),
            raddr=SimpleNamespace(ip="140.82.112.26", port=443),
            status="ESTABLISHED",
        ),
        SimpleNamespace(
            pid=1234,
            laddr=SimpleNamespace(ip="192.168.0.10", port=50002),
            raddr=SimpleNamespace(ip="140.82.112.26", port=443),
            status="ESTABLISHED",
        ),
        SimpleNamespace(
            pid=0,
            laddr=SimpleNamespace(ip="192.168.0.10", port=50003),
            raddr=SimpleNamespace(ip="140.82.112.26", port=443),
            status="TIME_WAIT",
        ),
        SimpleNamespace(
            pid=1234,
            laddr=SimpleNamespace(ip="192.168.0.10", port=50004),
            raddr=SimpleNamespace(ip="192.168.0.1", port=53),
            status="ESTABLISHED",
        ),
    ]

    monitor = NetworkMonitor(trusted_processes={"chrome.exe"})
    # Pre-populate DNS cache so test runs offline without network calls
    monitor._dns_cache["140.82.112.26"] = "github.com"

    results = monitor.scan()
    monitor.shutdown()

    assert len(results) == 1
    assert results[0]["process"] == "chrome.exe"
    assert results[0]["hostname"] == "github.com"
    assert results[0]["count"] == 2
    assert results[0]["roast"] == "SIZZLING"
