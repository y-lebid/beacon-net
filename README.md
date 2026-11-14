# 🥓 Beacon
[![CI](https://github.com/y-lebid/beacon-net/actions/workflows/ci.yml/badge.svg)](https://github.com/y-lebid/beacon-net/actions/workflows/ci.yml)

[Читати українською](./README.uk.md)

A lightweight terminal monitor for outbound network activity in real time, built with Python.

Beacon helps you instantly see which applications are currently connecting to the internet, which domains, IP addresses, and ports they use, and how suspicious each connection looks based on a simple roast-level system.

![Beacon Live Monitor](assets/preview.png)

## What it does

- **Real-time monitoring:** scans active IPv4/IPv6 sockets (`inet`) every second without flickering the terminal.
- **Non-blocking reverse DNS:** resolves external IP addresses into human-readable hostnames in a background thread pool with caching, so the UI never freezes.
- **Smart socket grouping:** deduplicates multiple connections from the same process to the same target into a single row with a socket counter (`x2`, `x8`).
- **Noise filtering:** automatically ignores loopback addresses, private subnets (`192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`), link-local traffic, and lingering `TIME_WAIT` sockets.
- **Persistent JSON whitelist:** stores trusted processes in `~/.beacon/whitelist.json` and lets you manage them from the CLI.
- **Roast-level scoring system:**
  - 🥩 `RAW (Idle)` — trusted process in an idle or closing state.
  - 🥓 `SIZZLING (Active)` — active `ESTABLISHED` connection from a trusted process on a standard port (`80`, `443`, `53`).
  - 🍳 `CRISPY (Custom Port)` — trusted process communicating over a non-standard port.
  - 🔥 `BURNT (Unknown)` — an untrusted or unrecognized process reaching out to the network.

## Installation and usage

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/y-lebid/beacon-net.git
   cd beacon-net
   python -m venv venv
   ```

2. Activate the environment and install the package:
   ```bash
   # Linux / macOS
   source venv/bin/activate

   # Windows
   venv\Scripts\activate

   pip install -e .
   ```

3. Run the monitor or manage your whitelist from the CLI:
   ```bash
   # Start the live monitor (default: 1-second refresh)
   beacon

   # Set a custom refresh interval
   beacon --interval 2

   # Show the whitelist path and trusted processes
   beacon --whitelist

   # Add a process to ~/.beacon/whitelist.json
   beacon --trust ProtonVPN.Client.exe
   ```

> **Note:** To resolve names for all system processes and services, run the terminal with elevated privileges (`sudo beacon` on Linux or as Administrator on Windows). Without elevated rights, protected processes may appear as `Restricted`.

## Development and testing

Install the development dependencies and run the test suite:

```bash
pip install -e ".[dev]"
pytest -v
```

## Roadmap to v1.0.0

- [x] Live terminal dashboard (`psutil` + `rich`)
- [x] Private subnet and `TIME_WAIT` socket filtering
- [x] Non-blocking background DNS resolution with caching
- [x] Socket grouping by process and target
- [x] Modular package layout (`src/beacon/`), CLI, and external `whitelist.json` (`v0.2.0-beta`)
- [ ] Connection history and anomaly detection with `sqlite3` (`v1.0.0`)
- [ ] Local tactical web dashboard with FastAPI + WebSockets (`v2.0.0`)
