from concurrent.futures import ThreadPoolExecutor
import ipaddress
import socket
import time
import psutil
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

TRUSTED_PROCESSES = {
    "chrome.exe", "chrome",
    "firefox.exe", "firefox",
    "code.exe", "code",
    "discord.exe", "discord",
    "telegram.exe", "telegram-desktop",
    "steam.exe", "steam",
    "eadesktop.exe", "eabackgroundservice.exe", "eacefsubprocess.exe",
    "msmpeng.exe", "svchost.exe", "systemd-resolve",
}

dns_cache: dict[str, str] = {}
pending_lookups: set[str] = set()
dns_executor = ThreadPoolExecutor(max_workers=4)


def _resolve_worker(ip: str) -> None:
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        dns_cache[ip] = hostname
    except (socket.herror, socket.gaierror, OSError):
        dns_cache[ip] = ip
    finally:
        pending_lookups.discard(ip)


def get_hostname(ip: str) -> str:
    """Returns cached PTR hostname or schedules a non-blocking background lookup."""
    if ip in dns_cache:
        return dns_cache[ip]
    if ip not in pending_lookups:
        pending_lookups.add(ip)
        dns_executor.submit(_resolve_worker, ip)
    return ip


def is_non_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_unspecified
    except ValueError:
        return True


def get_active_connections() -> list[dict]:
    """Collects active outbound connections and groups duplicate sockets per target."""
    grouped: dict[tuple, dict] = {}

    for conn in psutil.net_connections(kind="inet"):
        # Skip closed lingering sockets (usually owned by PID 0) and listening ports
        if not conn.raddr or conn.status == "TIME_WAIT":
            continue

        if is_non_public_ip(conn.raddr.ip):
            continue

        pid = conn.pid or 0
        proc_name = "System / Unknown"

        if pid:
            try:
                proc_name = psutil.Process(pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process terminated mid-scan or requires elevated privileges
                proc_name = f"Restricted (PID {pid})"

        remote_ip = conn.raddr.ip
        remote_port = conn.raddr.port
        hostname = get_hostname(remote_ip)

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
                "count": 1,
            }

    return sorted(grouped.values(), key=lambda x: (x["process"].lower(), x["hostname"]))


def get_roast_level(process_name: str, port: int, status: str) -> str:
    """Evaluates connection risk level based on process trust and target port."""
    if process_name.lower() not in TRUSTED_PROCESSES:
        return "[bold red]🔥 BURNT (Unknown)[/]"
    if port not in (80, 443, 53):
        return "[yellow]🍳 CRISPY (Custom Port)[/]"
    if status == "ESTABLISHED":
        return "[green]🥓 SIZZLING (Active)[/]"
    return "[dim]🥩 RAW (Idle)[/]"


def build_dashboard() -> Panel:
    """Builds the Rich live terminal table."""
    connections = get_active_connections()
    total_sockets = sum(item["count"] for item in connections)

    table = Table(
        box=box.SIMPLE_HEAD,
        expand=True,
        header_style="bold cyan",
    )

    table.add_column("PID", justify="right", style="dim", width=7)
    table.add_column("Process", style="bold white", min_width=18)
    table.add_column("Remote Target", style="bright_cyan")
    table.add_column("Sockets", justify="center", width=8)
    table.add_column("Status", width=13)
    table.add_column("Roast Level", width=22)

    for item in connections:
        if item["hostname"] != item["remote_ip"]:
            target = f"{item['hostname']} [dim]({item['remote_ip']}:{item['remote_port']})[/]"
        else:
            target = f"{item['remote_ip']}:{item['remote_port']}"

        count_badge = f"[bold yellow]x{item['count']}[/]" if item["count"] > 1 else "[dim]1[/]"
        roast = get_roast_level(item["process"], item["remote_port"], item["status"])

        table.add_row(
            str(item["pid"]),
            item["process"],
            target,
            count_badge,
            item["status"],
            roast,
        )

    title = (
        f"🥓 [bold yellow]BEACON[/] — Unique Targets: [bold green]{len(connections)}[/] "
        f"[dim](Total Sockets: {total_sockets})[/]"
    )
    subtitle = "[dim]Press Ctrl+C to stop sizzling[/]"

    return Panel(table, title=title, subtitle=subtitle, border_style="bright_black")


def main():
    console.clear()
    try:
        with Live(build_dashboard(), refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(1)
                live.update(build_dashboard())
    except KeyboardInterrupt:
        dns_executor.shutdown(wait=False, cancel_futures=True)
        console.print("\n[bold yellow]🥓 Beacon stopped. Stay safe![/]")


if __name__ == "__main__":
    main()