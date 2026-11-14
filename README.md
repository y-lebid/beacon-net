# 🥓 Beacon
[Читати українською](./README.uk.md)

A lightweight terminal monitor for outbound network activity in real time, built with Python.

Beacon helps you instantly see which applications are currently connecting to the internet, which domains, IP addresses, and ports they use, and how suspicious each connection looks based on a simple roast-level system.

![Beacon Live Monitor](assets/preview.png)

## What it does

- **Real-time monitoring:** scans active IPv4/IPv6 sockets (`inet`) every second without flickering the terminal.
- **Non-blocking Reverse DNS:** resolves external IP addresses into human-readable hostnames in a background thread pool with caching so the UI never freezes.
- **Smart socket grouping:** deduplicates multiple connections from the same process to the same target into a single row with a socket counter (`x2`, `x8`).
- **Noise filtering:** automatically ignores loopback addresses, private subnets (`192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`), link-local traffic, and lingering `TIME_WAIT` sockets.
- **Process mapping:** associates each connection with the originating application and its `PID`.
- **Roast-level scoring system:**
  - 🥩 `RAW (Idle)` — trusted process in an idle or closing state.
  - 🥓 `SIZZLING (Active)` — active `ESTABLISHED` connection from a trusted process on a standard port (`80`, `443`, `53`).
  - 🍳 `CRISPY (Custom Port)` — trusted process communicating over a non-standard port.
  - 🔥 `BURNT (Unknown)` — an untrusted or unrecognized process reaching out to the network.

## Installation and usage

1. Clone the repository:
   ```bash
   git clone https://github.com/y-lebid/beacon-net.git
   ```

2. Activate the environment and install dependencies:
   ```bash
   cd beacon-net
   python -m venv venv
   # Linux / macOS
   source venv/bin/activate

   # Windows
   venv\Scripts\activate

   pip install psutil rich
   ```

3. Run the monitor:
   ```bash
   python beacon.py
   ```

> Note: to display system processes and services correctly, run the script with administrator privileges (`sudo python beacon.py` on Linux or as Administrator on Windows).
> Without elevated rights, some system processes may appear as `Restricted`.

## Roadmap to v1.0.0

- [x] Live terminal dashboard (`psutil + rich`)
- [x] Background DNS resolution of IPs into hostnames with caching
- [x] Group sockets by process name
- [ ] Save connection history to SQLite
- [ ] Move `TRUSTED_PROCESSES` to an external config file and CLI interface