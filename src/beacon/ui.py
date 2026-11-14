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