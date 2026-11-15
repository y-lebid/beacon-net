from concurrent.futures import ThreadPoolExecutor
import ipaddress
import json
import subprocess
import sys
import psutil


class NetworkMonitor:
    """Collects active outbound sockets, resolves PTR records, and scores risk."""

    DNS_LOOKUP_TIMEOUT = 3.0

    def __init__(self, trusted_processes: set[str], max_dns_workers: int = 4):
        self.trusted_processes = {name.lower() for name in trusted_processes}
        self._dns_cache: dict[str, str] = {}
        self._pending_lookups: set[str] = set()
        self._executor = ThreadPoolExecutor(max_workers=max_dns_workers)

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _resolve_worker(self, ip: str) -> None:
        try:
            # Run libc's potentially unbounded resolver in a child process. This
            # keeps executor threads bounded and lets shutdown finish promptly.
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import json, socket, sys; print(json.dumps(socket.gethostbyaddr(sys.argv[1])[0]))",
                    ip,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=self.DNS_LOOKUP_TIMEOUT,
            )
            self._dns_cache[ip] = json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            self._dns_cache[ip] = ip
        finally:
            self._pending_lookups.discard(ip)

    def get_hostname(self, ip: str) -> str:
        if ip in self._dns_cache:
            return self._dns_cache[ip]
        if ip not in self._pending_lookups:
            self._pending_lookups.add(ip)
            self._executor.submit(self._resolve_worker, ip)
        return ip

    @staticmethod
    def is_non_public_ip(ip: str) -> bool:
        try:
            addr = ipaddress.ip_address(ip)
            return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_unspecified
        except ValueError:
            return True

    def get_roast_level(self, process_name: str, port: int, status: str) -> str:
        if process_name.lower() not in self.trusted_processes:
            return "BURNT"
        if port not in (80, 443, 53):
            return "CRISPY"
        if status == "ESTABLISHED":
            return "SIZZLING"
        return "RAW"

    def scan(self) -> list[dict]:
        """Scans active external connections and groups duplicate sockets per target."""
        grouped: dict[tuple, dict] = {}

        for conn in psutil.net_connections(kind="inet"):
            # Skip closed lingering sockets (usually owned by PID 0) and listening ports
            if not conn.raddr or conn.status == "TIME_WAIT":
                continue

            if self.is_non_public_ip(conn.raddr.ip):
                continue

            pid = conn.pid or 0
            proc_name = "System / Unknown"

            if pid:
                try:
                    proc_name = psutil.Process(pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = f"Restricted (PID {pid})"

            remote_ip = conn.raddr.ip
            remote_port = conn.raddr.port
            hostname = self.get_hostname(remote_ip)

            # Prevent table flooding from multi-socket apps like browsers
            key = (pid, proc_name, remote_ip, remote_port, conn.status)
            if key in grouped:
                grouped[key]["count"] += 1
            else:
                grouped[key] = {
                    "pid": pid,
                    "process": proc_name,
                    "remote_ip": remote_ip,
                    "hostname": hostname,
                    "remote_port": remote_port,
                    "status": conn.status,
                    "roast": self.get_roast_level(proc_name, remote_port, conn.status),
                    "count": 1,
                }

        return sorted(grouped.values(), key=lambda x: (x["process"].lower(), x["hostname"]))
