# 🥓 Beacon

[![CI](https://github.com/y-lebid/beacon-net/actions/workflows/ci.yml/badge.svg)](https://github.com/y-lebid/beacon-net/actions/workflows/ci.yml)

[Read in Ukrainian](./README.uk.md)

Beacon is a lightweight terminal monitor for outbound network activity. It shows active remote targets by process, resolves public IP addresses to hostnames in the background, and keeps a local history of observed targets.

![Beacon Live Monitor](assets/preview.png)
![Beacon Audit Mode](assets/history.png)

## Features

- **Live monitoring:** scans active IPv4 and IPv6 sockets with `psutil` and refreshes the Rich terminal dashboard once per second by default.
- **Noise filtering:** skips sockets without a remote address, `TIME_WAIT` sockets, and non-public IP addresses, including private, loopback, link-local, and unspecified addresses.
- **Background reverse DNS:** resolves hostnames without blocking the dashboard. Lookups run through a small thread pool, are cached, and have a three-second timeout.
- **Socket grouping:** combines sockets for the same process, remote IP, port, and status into one row with a socket count.
- **Process trust list:** stores trusted process names in `~/.beacon/whitelist.json`. The default list is created on first use and includes common desktop processes and `chronyd`.
- **Roast levels:**
  - 🥩 `RAW` — trusted process on a standard port in a state other than `ESTABLISHED`.
  - 🥓 `SIZZLING` — trusted process with an `ESTABLISHED` connection on port `80`, `443`, or `53`.
  - 🍳 `CRISPY` — trusted process using a different remote port.
  - 🔥 `BURNT` — process not present in the trust list, including processes Beacon cannot identify.
- **Connection history:** records process, remote IP and port, resolved hostname, roast level, first and last observation times (UTC), and an observation count in `~/.beacon/history.db`.
- **New-target marker:** shows `[NEW]` the first time a process/IP/port pair is recorded. Later DNS resolution updates the saved hostname without replacing it with the raw IP on subsequent scans.
- **History filters:** browse recent records, restrict the list to `BURNT` and `CRISPY`, and set a positive row limit.

History is local to the user account. The observation count is accumulated from socket counts on each scan; it is not a count of distinct TCP sessions.

## Install

Beacon requires Python 3.10 or later.

```bash
git clone https://github.com/y-lebid/beacon-net.git
cd beacon-net
python -m venv .venv
```

Activate the environment and install Beacon:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -e .
```

## CLI

```text
beacon [-h] [-i INTERVAL] [--trust PROCESS] [--whitelist]
       [--history] [--suspicious] [--limit N]
```

Examples:

```bash
# Start the live monitor (one-second refresh by default)
beacon

# Refresh every two seconds
beacon --interval 2

# Show the whitelist path and trusted process names
beacon --whitelist

# Trust a process name (comparison is case-insensitive)
beacon --trust ProtonVPN.Client.exe

# Show the 30 most recently observed history records
beacon --history

# Show up to 100 suspicious records
beacon --history --suspicious --limit 100
```

`--suspicious` filters history to `BURNT` and `CRISPY` records and is intended to be used with `--history`. `--limit` must be a positive integer and defaults to 30.

Beacon may need elevated permissions to read sockets owned by protected processes. Without them, those processes can appear as `Restricted (PID …)` and are classified as untrusted until their process name can be read.

## Development and tests

Install development dependencies and run the suite:

```bash
pip install -e ".[dev]"
pytest -v
```

GitHub Actions runs the test suite on Python 3.10 through 3.14 for pushes and pull requests targeting `master`.

## Roadmap

- [x] Live terminal dashboard, socket filtering, grouping, and background DNS
- [x] Persistent whitelist and roast-level classification
- [x] SQLite connection history, new-target marking, and suspicious-history filtering (v1.0.0)
- [ ] Local web dashboard with FastAPI and WebSockets (planned for v2.0.0)
