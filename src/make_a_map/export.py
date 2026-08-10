"""Atomic bilingual publication and machine-readable build manifest."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

from .contracts import MapSpec


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def atomic_output(root: Path, slug: str) -> Iterator[Path]:
    root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{slug}-", dir=root))
    try:
        yield staging
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def validate_png(path: Path, spec: MapSpec) -> None:
    with Image.open(path) as image:
        if image.size != spec.layout.pixel_size:
            raise ValueError(
                f"wrong PNG size for {path}: {image.size}, expected {spec.layout.pixel_size}"
            )
        dpi = image.info.get("dpi", (0, 0))
        if any(abs(value - spec.layout.dpi) > 1 for value in dpi):
            raise ValueError(f"wrong PNG DPI for {path}: {dpi}")


def finalize_build(
    staging: Path, destination: Path, spec: MapSpec, metadata: dict[str, object]
) -> Path:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = [
        spec.output_name(locale, extension)
        for locale in ("pt-BR", "en-US")
        for extension in spec.layout.formats
    ]
    missing = [name for name in expected if not (staging / name).is_file()]
    if missing:
        raise ValueError(f"incomplete bilingual build; missing: {missing}")
    for locale in ("pt-BR", "en-US"):
        if "png" in spec.layout.formats:
            validate_png(staging / spec.output_name(locale, "png"), spec)
    files = {
        name: {"sha256": file_hash(staging / name), "bytes": (staging / name).stat().st_size}
        for name in expected
    }
    for sidecar in sorted(staging.glob("caption_*.md")) + sorted(staging.glob("alt_*.txt")):
        files[sidecar.name] = {"sha256": file_hash(sidecar), "bytes": sidecar.stat().st_size}
    manifest = {
        "schema_version": spec.schema_version,
        "theme_version": spec.theme_version,
        "slug": spec.slug,
        "mode": spec.mode,
        "built_at": datetime.now(UTC).isoformat(),
        "locales": ["pt-BR", "en-US"],
        "layout": asdict(spec.layout),
        "files": files,
        "review": {
            "status": "draft",
            "data": None,
            "cartography": None,
            "translation": None,
            "final": None,
        },
        **metadata,
    }
    (staging / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if destination.exists():
        backup = destination.with_name(f".{destination.name}.previous")
        if backup.exists():
            shutil.rmtree(backup)
        destination.replace(backup)
        staging.replace(destination)
        shutil.rmtree(backup)
    else:
        staging.replace(destination)
    return destination
