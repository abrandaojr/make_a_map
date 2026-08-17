"""Verified, immutable acquisition of published cartographic sources."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import zlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile, ZipInfo

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = PROJECT_ROOT / "data" / "catalog" / "sources.json"
DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "cache"
REQUIRED_SHAPEFILE_SUFFIXES = frozenset({".shp", ".shx", ".dbf", ".prj"})


class DataIntegrityError(RuntimeError):
    """A cached or downloaded artifact does not match its declared contract."""


class OfflineDataError(FileNotFoundError):
    """Required verified data are absent while network access is disabled."""


@dataclass(frozen=True)
class DataSource:
    id: str
    title: str
    publisher: str
    edition: str
    url: str
    archive: str
    sha256: str
    size_bytes: int
    dataset_dir: str
    primary_file: str
    license: str
    license_url: str | None = None
    crs_original: str | None = None
    retrieved_on: str | None = None

    def __post_init__(self) -> None:
        if len(self.sha256) != 64 or any(character not in "0123456789abcdefABCDEF" for character in self.sha256):
            raise ValueError(f"invalid SHA-256 for {self.id}")
        if self.size_bytes <= 0:
            raise ValueError(f"size_bytes must be positive for {self.id}")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"source URL must be an unauthenticated HTTPS URL for {self.id}")
        for field_name in ("archive", "dataset_dir", "primary_file"):
            value = getattr(self, field_name)
            path = PurePosixPath(value)
            if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
                raise ValueError(f"{field_name} must be a safe relative path for {self.id}")

    @classmethod
    def from_mapping(cls, source_id: str, value: Mapping[str, Any]) -> DataSource:
        return cls(id=source_id, **value)


@dataclass(frozen=True)
class Provenance:
    source_id: str
    title: str
    publisher: str
    edition: str
    url: str
    sha256: str
    size_bytes: int
    archive_path: str
    data_path: str
    accessed_on: str
    crs_original: str | None
    license: str
    license_url: str | None

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


def load_catalog(path: Path | str = DEFAULT_CATALOG) -> dict[str, DataSource]:
    with Path(path).open(encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload.get("schema_version") != 1 or not isinstance(payload.get("sources"), dict):
        raise ValueError(f"Unsupported source catalog: {path}")
    return {key: DataSource.from_mapping(key, value) for key, value in payload["sources"].items()}


def sha256_file(path: Path | str, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_archive(path: Path, source: DataSource) -> None:
    size = path.stat().st_size
    if size != source.size_bytes:
        raise DataIntegrityError(
            f"Size mismatch for {source.id}: expected {source.size_bytes}, found {size}"
        )
    actual = sha256_file(path)
    if actual.lower() != source.sha256.lower():
        raise DataIntegrityError(
            f"SHA-256 mismatch for {source.id}: expected {source.sha256}, found {actual}"
        )


def _safe_member(info: ZipInfo) -> PurePosixPath:
    name = info.filename.replace("\\", "/")
    path = PurePosixPath(name)
    if (
        path.is_absolute()
        or not path.parts
        or ":" in path.parts[0]
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise DataIntegrityError(f"Unsafe ZIP member path: {info.filename!r}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise DataIntegrityError(
            f"Symbolic links are forbidden in source archives: {info.filename!r}"
        )
    return path


def _validate_members(zipped: ZipFile, source: DataSource) -> list[tuple[ZipInfo, PurePosixPath]]:
    members = [(info, _safe_member(info)) for info in zipped.infolist()]
    if not members:
        raise DataIntegrityError(f"Empty ZIP archive for {source.id}")
    if len(members) > 10_000:
        raise DataIntegrityError(f"Unreasonable ZIP member count for {source.id}")
    names = [str(path) for _, path in members]
    if len(names) != len(set(names)):
        raise DataIntegrityError(f"Duplicate ZIP member paths for {source.id}")
    expanded_size = sum(info.file_size for info, _ in members)
    if expanded_size > max(source.size_bytes * 25, 10_000_000):
        raise DataIntegrityError(f"Unreasonable expanded ZIP size for {source.id}")
    primary = PurePosixPath(source.primary_file)
    matching = [path for _, path in members if path.name == primary.name]
    if len(matching) != 1:
        raise DataIntegrityError(f"Expected exactly one {primary.name!r} in {source.id}")
    if primary.suffix.lower() == ".shp":
        stem = matching[0].with_suffix("")
        suffixes = {path.suffix.lower() for _, path in members if path.with_suffix("") == stem}
        missing = REQUIRED_SHAPEFILE_SUFFIXES - suffixes
        if missing:
            raise DataIntegrityError(
                f"Incomplete shapefile for {source.id}; missing: {', '.join(sorted(missing))}"
            )
    return members


def _extract_verified(archive: Path, target: Path, source: DataSource) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise DataIntegrityError(
            f"Immutable extraction directory exists but lacks the primary file: {target}"
        )
    try:
        with ZipFile(archive) as zipped:
            members = _validate_members(zipped, source)
            with tempfile.TemporaryDirectory(
                prefix=f".{target.name}-", dir=target.parent
            ) as temp_name:
                staging = Path(temp_name) / "payload"
                staging.mkdir()
                for info, relative in members:
                    destination = staging.joinpath(*relative.parts)
                    if info.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with zipped.open(info) as source_stream, destination.open("xb") as output:
                        shutil.copyfileobj(source_stream, output)
                primary_matches = list(staging.rglob(source.primary_file))
                if len(primary_matches) != 1:
                    raise DataIntegrityError(f"Extracted primary file is ambiguous for {source.id}")
                staging.replace(target)
                return target / primary_matches[0].relative_to(staging)
    except BadZipFile as error:
        raise DataIntegrityError(f"Invalid ZIP archive for {source.id}") from error


def _crc32_file(path: Path, chunk_size: int = 1024 * 1024) -> int:
    checksum = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            checksum = zlib.crc32(chunk, checksum)
    return checksum & 0xFFFFFFFF


def _verify_extraction(archive: Path, target: Path, source: DataSource) -> None:
    """Verify extracted source members against the already verified ZIP."""
    try:
        with ZipFile(archive) as zipped:
            members = _validate_members(zipped, source)
            components = [(info, relative) for info, relative in members if not info.is_dir()]
            for info, relative in components:
                extracted = target.joinpath(*relative.parts)
                if not extracted.is_file() or extracted.stat().st_size != info.file_size:
                    raise DataIntegrityError(f"Extracted member mismatch for {source.id}: {relative}")
                if _crc32_file(extracted) != info.CRC:
                    raise DataIntegrityError(f"Extracted member checksum mismatch for {source.id}: {relative}")
    except BadZipFile as error:
        raise DataIntegrityError(f"Invalid ZIP archive for {source.id}") from error


def _download_atomic(source: DataSource, destination: Path, timeout: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(source.url, headers={"User-Agent": "make-a-map/1 data-fetcher"})
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".part", dir=destination.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as output, urlopen(request, timeout=timeout) as response:
            shutil.copyfileobj(response, output)
            output.flush()
            os.fsync(output.fileno())
        _verify_archive(temp_path, source)
        # Never replace a cache object: another process may have completed first.
        try:
            os.link(temp_path, destination)
        except FileExistsError:
            _verify_archive(destination, source)
    finally:
        temp_path.unlink(missing_ok=True)


def fetch_source(
    source_id: str,
    *,
    raw_root: Path | str = DEFAULT_RAW_ROOT,
    catalog_path: Path | str = DEFAULT_CATALOG,
    offline: bool = False,
    timeout: int = 60,
) -> tuple[Path, Provenance]:
    """Return a verified primary dataset path and its reproducibility record.

    Cached archives are immutable: a mismatching file causes an error and is
    never silently replaced. Set ``offline=True`` (or ``MAKE_A_MAP_OFFLINE=1``)
    to guarantee that this function performs no network requests.
    """
    catalog = load_catalog(catalog_path)
    try:
        source = catalog[source_id]
    except KeyError as error:
        raise KeyError(f"Unknown data source {source_id!r}") from error
    root = Path(raw_root)
    archive = root / source.archive
    target = root / source.dataset_dir
    primary = target / source.primary_file
    no_network = offline or os.environ.get("MAKE_A_MAP_OFFLINE", "").lower() in {"1", "true", "yes"}

    if archive.exists():
        _verify_archive(archive, source)
    elif no_network:
        raise OfflineDataError(f"Verified archive unavailable offline: {archive}")
    else:
        _download_atomic(source, archive, timeout)

    # Immutable single-file sources (for example an edition-locked OSM PBF)
    # are consumed directly; ZIP sources retain the verified extraction path.
    if archive.suffix.lower() == ".pbf":
        primary = archive
    elif primary.exists():
        _verify_extraction(archive, target, source)
    else:
        primary = _extract_verified(archive, target, source)

    provenance = Provenance(
        source_id=source.id,
        title=source.title,
        publisher=source.publisher,
        edition=source.edition,
        url=source.url,
        sha256=source.sha256,
        size_bytes=source.size_bytes,
        archive_path=str(archive),
        data_path=str(primary),
        accessed_on=source.retrieved_on or datetime.now(UTC).date().isoformat(),
        crs_original=source.crs_original,
        license=source.license,
        license_url=source.license_url,
    )
    return primary, provenance


def ensure_source(source_id: str, **kwargs: Any) -> Path:
    """Compatibility convenience returning only the primary file path."""
    return fetch_source(source_id, **kwargs)[0]
