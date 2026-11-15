import argparse
import time
from rich.console import Console
from rich.live import Live

from beacon.config import WHITELIST_PATH, add_trusted_process, load_whitelist
from beacon.database import DB_PATH, ConnectionHistoryDB
from beacon.monitor import NetworkMonitor
from beacon.ui import build_dashboard, print_history_table

console = Console()


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


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
        help="Add a process name to the trusted whitelist and exit",
    )
    parser.add_argument(
        "--whitelist",
        action="store_true",
        help="Show the current trusted whitelist path and entries",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Display recorded outbound connection history from SQLite",
    )
    parser.add_argument(
        "--suspicious",
        action="store_true",
        help="Filter --history output to show only BURNT and CRISPY entries",
    )
    parser.add_argument(
        "--limit",
        type=_positive_int,
        default=30,
        help="Maximum number of rows to display with --history (default: 30)",
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

    db = ConnectionHistoryDB()

    if args.history:
        try:
            console.print(f"[dim]Database: {DB_PATH}[/]")
            records = db.get_recent_history(limit=args.limit, only_suspicious=args.suspicious)
            print_history_table(records, console)
        finally:
            db.close()
        return

    monitor = None
    try:
        monitor = NetworkMonitor(trusted_processes=whitelist)
        initial_scan = db.record_scan(monitor.scan())
        with Live(
            build_dashboard(initial_scan),
            refresh_per_second=1,
            screen=True,
            vertical_overflow="crop",
        ) as live:
            while True:
                time.sleep(args.interval)
                scanned = db.record_scan(monitor.scan())
                live.update(build_dashboard(scanned))
    except KeyboardInterrupt:
        console.print("\n[bold yellow]🥓 Beacon stopped. Stay safe![/]")
    finally:
        if monitor is not None:
            monitor.shutdown()
        db.close()


if __name__ == "__main__":
    main()
