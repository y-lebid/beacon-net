import os
from pathlib import Path
import tempfile


def ensure_secure_dir(directory: Path) -> None:
    """Creates config directory with owner-only permissions (0700) and rejects symlinks."""
    if directory.is_symlink():
        raise RuntimeError(f"Security error: {directory} cannot be a symlink.")

    directory.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(directory, 0o700)


def validate_no_symlink(filepath: Path) -> None:
    """Raises RuntimeError if the target file is a symbolic link."""
    if filepath.is_symlink():
        raise RuntimeError(f"Security error: {filepath} cannot be a symlink.")


def secure_file(filepath: Path) -> None:
    """Rejects symlinks and restricts file permissions to owner read/write (0600)."""
    validate_no_symlink(filepath)
    if filepath.exists() and os.name == "posix":
        os.chmod(filepath, 0o600)


def atomic_write_secure(filepath: Path, content: str) -> None:
    """Atomically writes content to a file with 0600 permissions on POSIX."""
    ensure_secure_dir(filepath.parent)
    validate_no_symlink(filepath)

    fd, tmp_path_str = tempfile.mkstemp(dir=filepath.parent, prefix=f".{filepath.name}.")
    tmp_path = Path(tmp_path_str)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_path, filepath)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise