import json
from pathlib import Path

from beacon.security import atomic_write_secure, ensure_secure_dir, secure_file

CONFIG_DIR = Path.home() / ".beacon"
WHITELIST_PATH = CONFIG_DIR / "whitelist.json"

DEFAULT_TRUSTED_PROCESSES = [
    "chrome",
    "chrome.exe",
    "msedge.exe",
    "firefox",
    "firefox.exe",
    "code",
    "code.exe",
    "discord",
    "discord.exe",
    "telegram",
    "telegram.exe",
    "steam",
    "steam.exe",
    "svchost.exe",
    "systemd-resolved",
    "chronyd",
    "networkmanager",
]


def _save_whitelist(processes: list[str], path: Path = WHITELIST_PATH) -> None:
    payload = json.dumps(sorted(set(processes)), indent=2) + "\n"
    atomic_write_secure(path, payload)


def load_whitelist(path: Path = WHITELIST_PATH) -> set[str]:
    """Loads trusted process names from JSON, initializing defaults securely if missing."""
    ensure_secure_dir(path.parent)

    if not path.exists():
        _save_whitelist(DEFAULT_TRUSTED_PROCESSES, path)
        return {p.lower() for p in DEFAULT_TRUSTED_PROCESSES}

    secure_file(path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("Whitelist JSON root must be a list")
        return {str(item).strip().lower() for item in data if str(item).strip()}
    except (json.JSONDecodeError, OSError, ValueError):
        return {p.lower() for p in DEFAULT_TRUSTED_PROCESSES}


def add_trusted_process(process_name: str, path: Path = WHITELIST_PATH) -> list[str]:
    """Adds a normalized process name to the persistent whitelist."""
    current = load_whitelist(path)
    normalized = process_name.strip().lower()
    if normalized:
        current.add(normalized)
    sorted_list = sorted(current)
    _save_whitelist(sorted_list, path)
    return sorted_list