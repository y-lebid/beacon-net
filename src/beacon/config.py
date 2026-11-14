import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".beacon"
WHITELIST_PATH = CONFIG_DIR / "whitelist.json"

DEFAULT_TRUSTED_PROCESSES = [
    "chrome.exe", "chrome",
    "firefox.exe", "firefox",
    "code.exe", "code",
    "discord.exe", "discord",
    "telegram.exe", "telegram-desktop",
    "steam.exe", "steam",
    "eadesktop.exe", "eabackgroundservice.exe", "eacefsubprocess.exe",
    "msmpeng.exe", "svchost.exe", "systemd-resolve",
]


def load_whitelist() -> set[str]:
    """Loads trusted process names from user config, creating defaults if missing."""
    if not WHITELIST_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        save_whitelist(set(DEFAULT_TRUSTED_PROCESSES))
        return {p.lower() for p in DEFAULT_TRUSTED_PROCESSES}

    try:
        data = json.loads(WHITELIST_PATH.read_text(encoding="utf-8"))
        return {str(item).lower() for item in data}
    except (json.JSONDecodeError, OSError):
        return {p.lower() for p in DEFAULT_TRUSTED_PROCESSES}


def save_whitelist(processes: set[str]) -> None:
    """Persists sorted trusted process names to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    sorted_list = sorted({p.lower() for p in processes})
    WHITELIST_PATH.write_text(json.dumps(sorted_list, indent=2), encoding="utf-8")


def add_trusted_process(process_name: str) -> set[str]:
    """Adds a process name to the persistent whitelist."""
    whitelist = load_whitelist()
    whitelist.add(process_name.strip().lower())
    save_whitelist(whitelist)
    return whitelist