from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

ROAST_BADGES = {
    "BURNT": "[bold red]🔥 BURNT (Unknown)[/]",
    "CRISPY": "[yellow]🍳 CRISPY (Custom Port)[/]",
    "SIZZLING": "[green]🥓 SIZZLING (Active)[/]",
    "RAW": "[dim]🥩 RAW (Idle)[/]",
}


def build_dashboard(connections: list[dict]) -> Panel:
    """Renders active connections into a Rich terminal panel."""
    total_sockets = sum(item["count"] for item in connections)

    table = Table(
        box=box.SIMPLE_HEAD,
        expand=True,
        header_style="bold cyan",
    )

    table.add_column("PID", justify="right", style="dim", width=6, no_wrap=True)
    table.add_column("Process", style="bold white", ratio=2, no_wrap=True, overflow="ellipsis")
    table.add_column("Remote Target", style="bright_cyan", ratio=4, no_wrap=True, overflow="ellipsis")
    table.add_column("Sockets", justify="center", width=7, no_wrap=True)
    table.add_column("Status", width=11, no_wrap=True)
    table.add_column("Roast Level", width=20, no_wrap=True)

    for item in connections:
        new_tag = "[bold magenta][NEW][/] " if item.get("is_new") else ""
        if item["hostname"] != item["remote_ip"]:
            target = f"{new_tag}{item['hostname']} [dim]({item['remote_ip']}:{item['remote_port']})[/]"
        else:
            target = f"{new_tag}{item['remote_ip']}:{item['remote_port']}"

        count_badge = f"[bold yellow]x{item['count']}[/]" if item["count"] > 1 else "[dim]1[/]"
        roast_badge = ROAST_BADGES.get(item["roast"], ROAST_BADGES["RAW"])

        table.add_row(
            str(item["pid"]),
            item["process"],
            target,
            count_badge,
            item["status"],
            roast_badge,
        )

    title = (
        f"🥓 [bold yellow]BEACON[/] — Unique Targets: [bold green]{len(connections)}[/] "
        f"[dim](Total Sockets: {total_sockets})[/]"
    )
    subtitle = "[dim]Press Ctrl+C to stop sizzling[/]"

    return Panel(table, title=title, subtitle=subtitle, border_style="bright_black")


def print_history_table(records: list[dict], console: Console) -> None:
    """Prints historical connection baselines from SQLite."""
    if not records:
        console.print("[yellow]No connection history found yet. Run `beacon` first to collect telemetry.[/]")
        return

    table = Table(
        title="📜 Beacon Connection History (UTC)",
        box=box.SIMPLE_HEAD,
        header_style="bold cyan",
    )

    table.add_column("Process", style="bold white", no_wrap=True, overflow="ellipsis")
    table.add_column("Remote Target", style="bright_cyan", ratio=1, no_wrap=True, overflow="ellipsis")
    table.add_column("Hits", justify="right", style="yellow", min_width=5, no_wrap=True, overflow="ellipsis")
    table.add_column("First Seen", style="dim", min_width=19, no_wrap=True, overflow="ellipsis")
    table.add_column("Last Seen", min_width=19, no_wrap=True, overflow="ellipsis")
    table.add_column("Roast Level", min_width=23, no_wrap=True, overflow="ellipsis")

    for row in records:
        if row["hostname"] != row["remote_ip"]:
            target = f"{row['hostname']} [dim]({row['remote_ip']}:{row['remote_port']})[/]"
        else:
            target = f"{row['remote_ip']}:{row['remote_port']}"

        roast_badge = ROAST_BADGES.get(row["roast_level"], ROAST_BADGES["RAW"])
        table.add_row(
            row["process"],
            target,
            str(row["hit_count"]),
            row["first_seen"],
            row["last_seen"],
            roast_badge,
        )

    console.print(table)
