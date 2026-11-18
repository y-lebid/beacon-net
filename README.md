# 🥓 Beacon

[![CI](https://github.com/y-lebid/beacon-net/actions/workflows/ci.yml/badge.svg)](https://github.com/y-lebid/beacon-net/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/y-lebid/beacon-net?label=Release)](https://github.com/y-lebid/beacon-net/releases)
[![License](https://img.shields.io/github/license/y-lebid/beacon-net?label=License&color=7CC4B0)](./LICENSE)
[![Stars](https://img.shields.io/github/stars/y-lebid/beacon-net?style=flat&logo=github&label=Stars)](https://github.com/y-lebid/beacon-net/stargazers)
[![Report Bug](https://img.shields.io/badge/Report-a%20bug-2ea44f?logo=github)](https://github.com/y-lebid/beacon-net/issues/new)
[![Monobank](https://img.shields.io/badge/Monobank-Donate%20🐈‍⬛-000000?style=flat&labelColor=1D2026&color=FA5255)](https://send.monobank.ua/jar/9pR25PQ1MV)

[Read in Ukrainian](./README.uk.md)

Beacon 1.1.0 is a lightweight terminal monitor for outbound network activity. It shows active remote targets by process, resolves public IP addresses to hostnames in the background, and keeps a local history of observed targets.

![Beacon Live Monitor](assets/preview.png)

## Features

- **Live monitoring:** scans active IPv4 and IPv6 sockets with `psutil` and refreshes the Rich terminal dashboard once per second by default.
- **Noise filtering:** skips sockets without a remote address, `TIME_WAIT` sockets, and non-public IP addresses, including private, loopback, link-local, and unspecified addresses.
- **Background reverse DNS:** resolves hostnames without blocking the dashboard. Lookups run through a small thread pool, are cached, and have a three-second timeout.
- **Socket grouping:** combines sockets for the same process, remote IP, port, and status into one row with a socket count.
- **Process trust list:** stores trusted process names in `~/.beacon/whitelist.json`. The default list is created on first use and includes common desktop and system processes (`chronyd`, `MsMpEng.exe`, and others).
- **Local data protection:** writes the whitelist atomically, rejects symlinked config/database targets, and on POSIX systems restricts the Beacon data directory to `0700` and files to `0600`.
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

### Prebuilt binaries (no Python required)

Download the matching binary and `SHA256SUMS.txt` from [GitHub Releases](https://github.com/y-lebid/beacon-net/releases/latest):

- Windows x64: `beacon-windows-x64.exe` and `beacon.bat`.
- Windows ARM64: `beacon-windows-arm64.exe` and `beacon.bat`.
- Linux x64/ARM64: the matching `.tar.gz` archive.

If you downloaded every release asset, verify them from that directory with:

```bash
sha256sum -c SHA256SUMS.txt
```

On Windows, compare the executable's hash in PowerShell:

```powershell
Get-FileHash .\beacon-windows-x64.exe -Algorithm SHA256
```

Compare the reported hash with the matching executable entry in `SHA256SUMS.txt` (use the ARM64 filename for an ARM64 build).

Run `beacon.bat` on Windows, or extract the Linux archive and run `./beacon`.

### Install from source (Python 3.10+ required)

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

![Beacon Audit Mode](assets/history.png)

### Security and data storage

The whitelist and database are stored under `~/.beacon`. On POSIX systems, Beacon sets the directory permissions to `0700` and the whitelist, database, and existing SQLite sidecar files to `0600`. Whitelist updates use an atomic replacement. Beacon refuses to use the config directory, whitelist, database, or database sidecars when the target itself is a symlink. On Windows, the files use the permissions inherited from the user's account and directory ACLs.

Beacon may need elevated permissions to read sockets owned by protected processes. Without them, those processes can appear as `Restricted (PID …)` and are classified as untrusted until their process name can be read.

## Development and tests

Install development dependencies and run the suite:

```bash
pip install -e ".[dev]"
pytest -v
```

GitHub Actions runs pytest on Python 3.10 through 3.14 and runs Bandit and `pip-audit` on pushes and pull requests targeting `main` or `master`. Pushing a `v*` tag builds Windows x64/ARM64 and Linux x64/ARM64 release artifacts, smoke-tests the binaries, and attaches them with SHA-256 checksums.

## Roadmap

- [x] Live terminal dashboard, socket filtering, grouping, and background DNS
- [x] Persistent whitelist and roast-level classification
- [x] SQLite connection history, new-target marking, suspicious-history filtering, and local data hardening (v1.1.0)
- [ ] Local web dashboard with FastAPI and WebSockets (planned for v2.0.0)
