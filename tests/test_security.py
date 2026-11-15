import os
from pathlib import Path
import pytest

from beacon.config import add_trusted_process, load_whitelist
from beacon.database import ConnectionHistoryDB
from beacon.security import atomic_write_secure, ensure_secure_dir


def test_atomic_write_and_permissions(tmp_path: Path):
    cfg_dir = tmp_path / ".beacon"
    wl_file = cfg_dir / "whitelist.json"

    load_whitelist(wl_file)
    assert wl_file.exists()

    if os.name == "posix":
        dir_mode = cfg_dir.stat().st_mode & 0o777
        file_mode = wl_file.stat().st_mode & 0o777
        assert dir_mode == 0o700
        assert file_mode == 0o600


def test_rejects_symlink_directory(tmp_path: Path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    symlink_dir = tmp_path / "fake_beacon"

    try:
        symlink_dir.symlink_to(real_dir, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation requires elevated privileges on this Windows host")

    with pytest.raises(RuntimeError, match="symlink"):
        ensure_secure_dir(symlink_dir)


def test_rejects_symlink_file(tmp_path: Path):
    target_file = tmp_path / "target.txt"
    target_file.write_text("sensitive", encoding="utf-8")
    symlink_file = tmp_path / "whitelist.json"

    try:
        symlink_file.symlink_to(target_file)
    except OSError:
        pytest.skip("Symlink creation requires elevated privileges on this Windows host")

    with pytest.raises(RuntimeError, match="symlink"):
        atomic_write_secure(symlink_file, "[]")


def test_database_hardens_permissions(tmp_path: Path):
    db_file = tmp_path / ".beacon" / "history.db"
    db = ConnectionHistoryDB(db_file)
    db.close()

    if os.name == "posix":
        assert (db_file.stat().st_mode & 0o777) == 0o600