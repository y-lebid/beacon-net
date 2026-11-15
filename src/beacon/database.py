from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from beacon.config import CONFIG_DIR
from beacon.security import ensure_secure_dir, secure_file

DB_PATH = CONFIG_DIR / "history.db"


class ConnectionHistoryDB:
    """SQLite persistence layer for tracking outbound connection baselines and anomalies."""

    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)
        if str(self.db_path) != ":memory:":
            ensure_secure_dir(self.db_path.parent)
            secure_file(self.db_path)

        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._known_pairs: set[tuple[str, str, int]] = set()
        try:
            self._init_schema()
            self._normalize_existing_process_names()
            self._load_baseline()
            if str(self.db_path) != ":memory:":
                self._harden_db_files()
        except Exception:
            self._conn.close()
            raise

    def _harden_db_files(self) -> None:
        """Applies owner-only permissions to the database and SQLite sidecars."""
        for suffix in ("", "-wal", "-shm"):
            target = Path(f"{self.db_path}{suffix}")
            if target.exists():
                secure_file(target)

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS connection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process TEXT NOT NULL,
                    remote_ip TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    remote_port INTEGER NOT NULL,
                    roast_level TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    hit_count INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(process, remote_ip, remote_port)
                );
                """
            )
            self._conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_history_last_seen
                ON connection_history(last_seen DESC);
                """
            )

    def _load_baseline(self) -> None:
        """Loads previously seen (process, ip, port) tuples into memory for O(1) anomaly checks."""
        cursor = self._conn.execute(
            "SELECT process, remote_ip, remote_port FROM connection_history;"
        )
        self._known_pairs = {
            (row["process"].lower(), row["remote_ip"], row["remote_port"])
            for row in cursor.fetchall()
        }

    def _normalize_existing_process_names(self) -> None:
        """Merges legacy rows that differ only by process-name casing."""
        rows = [dict(row) for row in self._conn.execute(
            "SELECT process, remote_ip, hostname, remote_port, roast_level, first_seen, last_seen, hit_count "
            "FROM connection_history;"
        )]
        grouped: dict[tuple[str, str, int], list[dict]] = {}
        for row in rows:
            key = (row["process"].lower(), row["remote_ip"], row["remote_port"])
            grouped.setdefault(key, []).append(row)

        if all(row["process"] == row["process"].lower() for row in rows) and len(grouped) == len(rows):
            return

        merged = []
        for (process, remote_ip, remote_port), variants in grouped.items():
            latest = max(variants, key=lambda row: row["last_seen"])
            named_hosts = [row for row in variants if row["hostname"] != remote_ip]
            hostname = max(named_hosts, key=lambda row: row["last_seen"])["hostname"] if named_hosts else remote_ip
            merged.append((
                process, remote_ip, hostname, remote_port, latest["roast_level"],
                min(row["first_seen"] for row in variants),
                max(row["last_seen"] for row in variants),
                sum(row["hit_count"] for row in variants),
            ))

        with self._conn:
            self._conn.execute("DELETE FROM connection_history;")
            self._conn.executemany(
                """
                INSERT INTO connection_history (
                    process, remote_ip, hostname, remote_port, roast_level,
                    first_seen, last_seen, hit_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                merged,
            )

    def record_scan(self, connections: list[dict]) -> list[dict]:
        """Upserts active connections and flags entries never seen before as `is_new=True`."""
        if not connections:
            return connections

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        upsert_sql = """
            INSERT INTO connection_history (
                process, remote_ip, hostname, remote_port, roast_level, first_seen, last_seen, hit_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(process, remote_ip, remote_port) DO UPDATE SET
                hostname = CASE
                    WHEN excluded.hostname != excluded.remote_ip THEN excluded.hostname
                    ELSE connection_history.hostname
                END,
                roast_level = excluded.roast_level,
                last_seen = excluded.last_seen,
                hit_count = connection_history.hit_count + excluded.hit_count;
        """

        rows_to_upsert = []
        pairs_in_scan: set[tuple[str, str, int]] = set()
        for item in connections:
            pair = (item["process"].lower(), item["remote_ip"], item["remote_port"])
            is_new = pair not in self._known_pairs and pair not in pairs_in_scan
            item["is_new"] = is_new
            pairs_in_scan.add(pair)

            rows_to_upsert.append(
                (
                    pair[0],
                    item["remote_ip"],
                    item["hostname"],
                    item["remote_port"],
                    item["roast"],
                    now,
                    now,
                    item["count"],
                )
            )

        with self._conn:
            self._conn.executemany(upsert_sql, rows_to_upsert)

        # Keep the in-memory baseline aligned with committed database state.
        self._known_pairs.update(pairs_in_scan)

        return connections

    def get_recent_history(self, limit: int = 30, only_suspicious: bool = False) -> list[dict]:
        """Fetches historical records ordered by most recent activity."""
        if limit <= 0:
            raise ValueError("limit must be a positive integer")
        query = """
            SELECT process, remote_ip, hostname, remote_port, roast_level, first_seen, last_seen, hit_count
            FROM connection_history
        """
        params: list = []
        if only_suspicious:
            query += " WHERE roast_level IN ('BURNT', 'CRISPY')"

        query += " ORDER BY last_seen DESC LIMIT ?;"
        params.append(limit)

        cursor = self._conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        self._conn.close()
