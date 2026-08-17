"""Atomic output helpers for the final bilingual map collection."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def file_hash(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def atomic_output(root: Path, slug: str) -> Iterator[Path]:
    """Yield a temporary directory beside its eventual destination."""
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{slug}-", dir=root))
    try:
        yield staging
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def promote_output(staging: Path, destination: Path) -> None:
    """Promote a complete directory and restore the previous build on failure."""
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        staging.replace(destination)
        return
    backup = Path(tempfile.mkdtemp(prefix=f".{destination.name}-backup-", dir=destination.parent))
    backup.rmdir()
    destination.replace(backup)
    try:
        staging.replace(destination)
    except BaseException:
        if not destination.exists() and backup.exists():
            backup.replace(destination)
        raise
    else:
        shutil.rmtree(backup)
