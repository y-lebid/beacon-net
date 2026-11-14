import argparse
import time
from rich.console import Console
from rich.live import Live

from beacon.config import WHITELIST_PATH, add_trusted_process, load_whitelist
from beacon.monitor import NetworkMonitor
from beacon.ui import build_dashboard

console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="beacon",
        description="Real-time outbound process network monitor",
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=1.0,
        help="Refresh interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--trust",
        metavar="PROCESS",
        help="Add a process name to the trusted whitelist and exit (e.g. --trust ProtonVPN.Client.exe)",
    )
    parser.add_argument(
        "--whitelist",
        action="store_true",
        help="Show the current trusted whitelist path and entries",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.trust:
        updated = add_trusted_process(args.trust)
        console.print(f"[green]✓ Added [bold]{args.trust}[/bold] to whitelist ({len(updated)} total).[/]")
        return

    whitelist = load_whitelist()

    if args.whitelist:
        console.print(f"[cyan]Whitelist file:[/] {WHITELIST_PATH}")
        for proc in sorted(whitelist):
            console.print(f"  • {proc}")
        return

    monitor = NetworkMonitor(trusted_processes=whitelist)
    console.clear()

    try:
        with Live(build_dashboard(monitor.scan()), refresh_per_second=1, screen=True) as live:
            while True:
                time.sleep(args.interval)
                live.update(build_dashboard(monitor.scan()))
    except KeyboardInterrupt:
        monitor.shutdown()
        console.print("\n[bold yellow]🥓 Beacon stopped. Stay safe![/]")


if __name__ == "__main__":
    main()