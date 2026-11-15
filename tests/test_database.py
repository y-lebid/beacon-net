import sqlite3

import pytest

from beacon.database import ConnectionHistoryDB


@pytest.fixture
def db():
    history = ConnectionHistoryDB(":memory:")
    try:
        yield history
    finally:
        history.close()


def test_record_scan_detects_new_and_updates_existing():
    db = ConnectionHistoryDB(":memory:")

    first_batch = [
        {
            "pid": 100,
            "process": "chrome.exe",
            "remote_ip": "140.82.112.26",
            "hostname": "140.82.112.26",
            "remote_port": 443,
            "status": "ESTABLISHED",
            "roast": "SIZZLING",
            "count": 2,
        }
    ]

    res1 = db.record_scan(first_batch)
    assert res1[0]["is_new"] is True

    # Second scan: same target, now DNS resolved
    second_batch = [
        {
            "pid": 100,
            "process": "chrome.exe",
            "remote_ip": "140.82.112.26",
            "hostname": "github.com",
            "remote_port": 443,
            "status": "ESTABLISHED",
            "roast": "SIZZLING",
            "count": 3,
        }
    ]

    res2 = db.record_scan(second_batch)
    assert res2[0]["is_new"] is False

    history = db.get_recent_history(limit=10)
    assert len(history) == 1
    assert history[0]["hostname"] == "github.com"
    assert history[0]["hit_count"] == 5
    db.close()


def test_suspicious_history_filter():
    db = ConnectionHistoryDB(":memory:")

    batch = [
        {
            "pid": 100,
            "process": "chrome.exe",
            "remote_ip": "1.1.1.1",
            "hostname": "one.one.one.one",
            "remote_port": 443,
            "status": "ESTABLISHED",
            "roast": "SIZZLING",
            "count": 1,
        },
        {
            "pid": 999,
            "process": "unknown_agent.exe",
            "remote_ip": "185.100.10.5",
            "hostname": "185.100.10.5",
            "remote_port": 4444,
            "status": "ESTABLISHED",
            "roast": "BURNT",
            "count": 1,
        },
    ]

    db.record_scan(batch)

    suspicious = db.get_recent_history(only_suspicious=True)
    assert len(suspicious) == 1
    assert suspicious[0]["process"] == "unknown_agent.exe"
    assert suspicious[0]["roast_level"] == "BURNT"
    db.close()


def test_process_name_case_is_normalized_and_duplicate_scan_is_not_new(db):
    batch = [
        {
            "process": "Chrome.exe", "remote_ip": "140.82.112.26", "hostname": "140.82.112.26",
            "remote_port": 443, "roast": "SIZZLING", "count": 1,
        },
        {
            "process": "chrome.EXE", "remote_ip": "140.82.112.26", "hostname": "github.com",
            "remote_port": 443, "roast": "SIZZLING", "count": 2,
        },
    ]

    recorded = db.record_scan(batch)

    assert [item["is_new"] for item in recorded] == [True, False]
    history = db.get_recent_history()
    assert len(history) == 1
    assert history[0]["process"] == "chrome.exe"
    assert history[0]["hostname"] == "github.com"
    assert history[0]["hit_count"] == 3


def test_failed_upsert_does_not_mark_pair_as_known(db):
    batch = [{
        "process": "chrome.exe", "remote_ip": "140.82.112.26", "hostname": "140.82.112.26",
        "remote_port": 443, "roast": "SIZZLING", "count": 1,
    }]
    with db._conn:
        db._conn.execute(
            """CREATE TRIGGER reject_history_insert BEFORE INSERT ON connection_history
               BEGIN SELECT RAISE(ABORT, 'forced insert failure'); END;"""
        )

    with pytest.raises(sqlite3.IntegrityError):
        db.record_scan(batch)

    with db._conn:
        db._conn.execute("DROP TRIGGER reject_history_insert;")
    assert db.record_scan(batch)[0]["is_new"] is True


def test_legacy_case_variants_are_merged(tmp_path):
    path = tmp_path / "history.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            """CREATE TABLE connection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, process TEXT NOT NULL, remote_ip TEXT NOT NULL,
                hostname TEXT NOT NULL, remote_port INTEGER NOT NULL, roast_level TEXT NOT NULL,
                first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, hit_count INTEGER NOT NULL DEFAULT 1,
                UNIQUE(process, remote_ip, remote_port)
            );"""
        )
        conn.executemany(
            """INSERT INTO connection_history
               (process, remote_ip, hostname, remote_port, roast_level, first_seen, last_seen, hit_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
            [
                ("Chrome.exe", "140.82.112.26", "140.82.112.26", 443, "SIZZLING", "2025-01-01", "2025-01-02", 2),
                ("chrome.EXE", "140.82.112.26", "github.com", 443, "SIZZLING", "2025-01-02", "2025-01-03", 3),
            ],
        )

    history_db = ConnectionHistoryDB(path)
    try:
        records = history_db.get_recent_history()
        assert len(records) == 1
        assert records[0]["process"] == "chrome.exe"
        assert records[0]["hostname"] == "github.com"
        assert records[0]["first_seen"] == "2025-01-01"
        assert records[0]["hit_count"] == 5
        assert history_db.record_scan([{
            "process": "CHROME.EXE", "remote_ip": "140.82.112.26", "hostname": "github.com",
            "remote_port": 443, "roast": "SIZZLING", "count": 1,
        }])[0]["is_new"] is False
    finally:
        history_db.close()


def test_history_limit_must_be_positive(db):
    with pytest.raises(ValueError, match="positive"):
        db.get_recent_history(limit=0)
