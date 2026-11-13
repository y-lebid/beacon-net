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
    "svchost.exe", "systemd-resolve",
}


def is_local_ip(ip: str) -> bool:
    return ip.startswith("127.") or ip in ("::1", "0.0.0.0", "::")


def get_active_connections() -> list[dict]:
    connections_data = []

    for conn in psutil.net_connections(kind="inet"):
        if not conn.raddr or is_local_ip(conn.raddr.ip):
            continue

        pid = conn.pid
        proc_name = "System / Unknown"

        if pid:
            try:
                proc_name = psutil.Process(pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                proc_name = f"Restricted (PID {pid})"

        connections_data.append({
            "pid": pid or 0,
            "process": proc_name,
            "local": f"{conn.laddr.ip}:{conn.laddr.port}",
            "remote_ip": conn.raddr.ip,
            "remote_port": conn.raddr.port,
            "status": conn.status,
        })

    return sorted(connections_data, key=lambda x: (x["process"].lower(), x["remote_ip"]))


def get_roast_level(process_name: str, port: int, status: str) -> str:
    if process_name.lower() not in TRUSTED_PROCESSES:
        return "[bold red]🔥 BURNT (Unknown)[/]"
    if port not in (80, 443, 53):
        return "[yellow]🍳 CRISPY (Custom Port)[/]"
    if status == "ESTABLISHED":
        return "[green]🥓 SIZZLING (Active)[/]"
    return "[dim]🥩 RAW (Idle)[/]"


def build_dashboard() -> Panel:
    connections = get_active_connections()

    table = Table(
        box=box.SIMPLE_HEAD,
        expand=True,
        header_style="bold cyan",
    )

    table.add_column("PID", justify="right", style="dim", width=7)
    table.add_column("Process", style="bold white", min_width=18)
    table.add_column("Remote Target", style="blue")
    table.add_column("Status", width=13)
    table.add_column("Roast Level", width=22)

    for item in connections:
        target = f"{item['remote_ip']}:{item['remote_port']}"
        roast = get_roast_level(item["process"], item["remote_port"], item["status"])

        table.add_row(
            str(item["pid"]),
            item["process"],
            target,
            item["status"],
            roast,
        )

    title = f"🥓 [bold yellow]BEACON[/] — Active Egress Connections: [bold green]{len(connections)}[/]"
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
        console.print("\n[bold yellow]🥓 Beacon stopped. Stay safe![/]")


if __name__ == "__main__":
    main()