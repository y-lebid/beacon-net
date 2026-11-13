# 🥓 Beacon
[Читати українською](./README.uk.md)

A lightweight terminal monitor for outbound network activity in real time, built with Python.

Beacon helps you instantly see which applications are currently connecting to the internet, which IP addresses and ports they use, and how suspicious each connection looks based on a simple roast-level system.

## What it does

- **Real-time monitoring:** checks active IPv4/IPv6 sockets (`inet`) every second without flickering the terminal.
- **Noise filtering:** automatically ignores local loopback traffic (`127.0.0.1`, `::1`, `0.0.0.0`, `::`) and keeps only real external connections.
- **Process mapping:** associates each connection with the originating application and its `PID`.
- **Roast-level scoring system:**
  - 🥩 `RAW (Idle)` — trusted process in idle state.
  - 🥓 `SIZZLING (Active)` — active `ESTABLISHED` connection from a trusted process on a common port (`80`, `443`, `53`).
  - 🍳 `CRISPY (Custom Port)` — trusted process communicating on a custom port.
  - 🔥 `BURNT (Unknown)` — an untrusted process is reaching out to the network.

## Installation and usage

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/<your-username>/beacon-net.git
   cd beacon-net
   python -m venv venv
   ```

2. Activate the environment and install dependencies (`psutil` and `rich`):
   ```bash
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
- [ ] Background DNS resolution of IPs into hostnames with caching
- [ ] Group sockets by process name
- [ ] Save connection history to SQLite
- [ ] Move `TRUSTED_PROCESSES` to an external config file and CLI interface