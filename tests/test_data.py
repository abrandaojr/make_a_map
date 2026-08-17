import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from make_a_map.data import DataIntegrityError, fetch_source, sha256_file


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    with ZipFile(path, "w") as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def _catalog(path: Path, archive: Path, digest: str, *, primary: str = "shape.shp") -> Path:
    payload = {
        "schema_version": 1,
        "sources": {
            "fixture": {
                "title": "Synthetic boundaries",
                "publisher": "Test fixture",
                "edition": "1",
                "url": "https://example.invalid/fixture.zip",
                "archive": archive.name,
                "sha256": digest,
                "size_bytes": archive.stat().st_size,
                "dataset_dir": "fixture-v1",
                "primary_file": primary,
                "license": "Public domain fixture",
                "crs_original": "EPSG:4674",
            }
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_sha256_file_matches_known_content(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"immutable cartography")

    assert sha256_file(artifact) == hashlib.sha256(b"immutable cartography").hexdigest()


def test_offline_fetch_verifies_and_extracts_complete_shapefile(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    archive = raw / "fixture.zip"
    _write_zip(
        archive,
        {suffix: b"fixture" for suffix in ("shape.shp", "shape.shx", "shape.dbf", "shape.prj")},
    )
    catalog = _catalog(tmp_path / "sources.json", archive, sha256_file(archive))

    primary, provenance = fetch_source("fixture", raw_root=raw, catalog_path=catalog, offline=True)

    assert primary.is_file()
    assert primary.parent == raw / "fixture-v1"
    assert provenance.sha256 == sha256_file(archive)
    assert provenance.crs_original == "EPSG:4674"


def test_offline_fetch_verifies_and_extracts_raster(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    archive = raw / "fixture.zip"
    _write_zip(archive, {"relief/terrain.tif": b"raster", "relief/terrain.tfw": b"world-file"})
    catalog = _catalog(
        tmp_path / "sources.json", archive, sha256_file(archive), primary="terrain.tif"
    )

    primary, provenance = fetch_source("fixture", raw_root=raw, catalog_path=catalog, offline=True)

    assert primary.read_bytes() == b"raster"
    assert provenance.sha256 == sha256_file(archive)


def test_offline_fetch_rejects_modified_extracted_component(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    archive = raw / "fixture.zip"
    _write_zip(
        archive,
        {suffix: b"fixture" for suffix in ("shape.shp", "shape.shx", "shape.dbf", "shape.prj")},
    )
    catalog = _catalog(tmp_path / "sources.json", archive, sha256_file(archive))
    primary, _ = fetch_source("fixture", raw_root=raw, catalog_path=catalog, offline=True)
    primary.with_suffix(".dbf").write_bytes(b"tampered")

    with pytest.raises(DataIntegrityError, match="Extracted member"):
        fetch_source("fixture", raw_root=raw, catalog_path=catalog, offline=True)


def test_offline_fetch_rejects_hash_mismatch_without_replacing_cache(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    archive = raw / "fixture.zip"
    _write_zip(archive, {"shape.shp": b"unexpected"})
    original = archive.read_bytes()
    catalog = _catalog(tmp_path / "sources.json", archive, "0" * 64)

    with pytest.raises(DataIntegrityError, match="SHA-256 mismatch"):
        fetch_source("fixture", raw_root=raw, catalog_path=catalog, offline=True)

    assert archive.read_bytes() == original


def test_offline_fetch_returns_verified_single_file_source(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    archive = raw / "fixture.pbf"
    archive.parent.mkdir()
    archive.write_bytes(b"edition-locked osm fixture")
    payload = {
        "schema_version": 1,
        "sources": {
            "fixture": {
                "title": "OSM fixture",
                "publisher": "Test fixture",
                "edition": "1",
                "url": "https://example.invalid/fixture.pbf",
                "archive": archive.name,
                "sha256": sha256_file(archive),
                "size_bytes": archive.stat().st_size,
                "dataset_dir": "unused",
                "primary_file": archive.name,
                "license": "ODbL fixture",
            }
        },
    }
    catalog = tmp_path / "sources.json"
    catalog.write_text(json.dumps(payload), encoding="utf-8")

    primary, provenance = fetch_source("fixture", raw_root=raw, catalog_path=catalog, offline=True)

    assert primary == archive
    assert provenance.data_path == str(archive)


@pytest.mark.parametrize("unsafe_name", ["../escape.shp", "/absolute/escape.shp", "C:/escape.shp"])
def test_zip_path_traversal_is_rejected(tmp_path: Path, unsafe_name: str) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    archive = raw / "fixture.zip"
    _write_zip(
        archive,
        {
            unsafe_name: b"bad",
            "shape.shp": b"fixture",
            "shape.shx": b"fixture",
            "shape.dbf": b"fixture",
            "shape.prj": b"fixture",
        },
    )
    catalog = _catalog(tmp_path / "sources.json", archive, sha256_file(archive))

    with pytest.raises(DataIntegrityError, match="Unsafe ZIP member path"):
        fetch_source("fixture", raw_root=raw, catalog_path=catalog, offline=True)

    assert not (tmp_path / "escape.shp").exists()
