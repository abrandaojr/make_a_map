"""Immutable public contracts for reproducible map definitions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal
from urllib.parse import urlparse

from .i18n import Locale, TranslationCatalog, format_number

Mode = Literal["scientific", "editorial"]
OutputFormat = Literal["png", "pdf", "svg", "tiff"]


def _nonempty(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} cannot be empty")


@dataclass(frozen=True, slots=True)
class Quantity:
    """A numeric quantity whose unit text comes from the catalog."""

    value: int | float | Decimal
    unit_key: str | None = None
    decimals: int = 0

    def __post_init__(self) -> None:
        number = Decimal(str(self.value))
        if not number.is_finite():
            raise ValueError("quantity value must be finite")
        if self.decimals < 0:
            raise ValueError("quantity decimals must be non-negative")
        if self.unit_key is not None:
            _nonempty("quantity unit_key", self.unit_key)

    def format(self, locale: Locale, catalog: TranslationCatalog | None = None) -> str:
        value = format_number(self.value, locale, self.decimals)
        if self.unit_key is None:
            return value
        if catalog is None:
            raise ValueError("a translation catalog is required when quantity has a unit_key")
        return f"{value} {catalog.get(locale, self.unit_key)}"


@dataclass(frozen=True, slots=True)
class Statistic:
    """An optional, typed callout shared by both language variants."""

    label_key: str
    quantity: Quantity
    note_key: str | None = None

    def __post_init__(self) -> None:
        _nonempty("statistic label_key", self.label_key)
        if self.note_key is not None:
            _nonempty("statistic note_key", self.note_key)

    def format(self, locale: Locale, catalog: TranslationCatalog) -> tuple[str, str, str | None]:
        return (
            catalog.get(locale, self.label_key),
            self.quantity.format(locale, catalog),
            catalog.get(locale, self.note_key) if self.note_key else None,
        )


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """Provenance required for an immutable source edition."""

    source_id: str
    publisher: str
    product: str
    edition: str
    url: str
    accessed: date
    original_crs: str
    sha256: str | None = None

    def __post_init__(self) -> None:
        for name in ("source_id", "publisher", "product", "edition", "url", "original_crs"):
            _nonempty(name, getattr(self, name))
        parsed = urlparse(self.url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise ValueError(f"source URL must be absolute HTTP(S): {self.url!r}")
        if self.sha256 is not None:
            digest = self.sha256.lower()
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("source sha256 must contain exactly 64 hexadecimal characters")
            object.__setattr__(self, "sha256", digest)


@dataclass(frozen=True, slots=True)
class LayoutSpec:
    width_inches: float = 7.5
    height_inches: float = 7.5
    dpi: int = 300
    formats: tuple[OutputFormat, ...] = ("png", "pdf", "svg")
    globe_inset: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "formats", tuple(self.formats))
        if (self.width_inches, self.height_inches) != (7.5, 7.5):
            raise ValueError("v1 figures must be exactly 7.5 x 7.5 inches")
        if self.dpi not in {300, 600}:
            raise ValueError("dpi must be 300 or 600")
        if not self.globe_inset:
            raise ValueError("the orthographic globe inset is mandatory")
        if not self.formats or len(set(self.formats)) != len(self.formats):
            raise ValueError("formats must be a non-empty tuple without duplicates")
        unsupported = set(self.formats) - {"png", "pdf", "svg", "tiff"}
        if unsupported:
            raise ValueError(f"unsupported output formats: {sorted(unsupported)}")

    @property
    def pixel_size(self) -> tuple[int, int]:
        return (round(self.width_inches * self.dpi), round(self.height_inches * self.dpi))


@dataclass(frozen=True, slots=True)
class MapSpec:
    slug: str
    mode: Mode
    crs: str
    catalog: TranslationCatalog
    sources: tuple[SourceSpec, ...]
    statistics: tuple[Statistic, ...] = ()
    layout: LayoutSpec = field(default_factory=LayoutSpec)
    schema_version: str = "1.0"
    theme_version: str = "1.0"

    def __post_init__(self) -> None:
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "statistics", tuple(self.statistics))
        _nonempty("slug", self.slug)
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", self.slug) is None:
            raise ValueError("slug must contain only lowercase ASCII letters, digits, and hyphens")
        if self.mode not in {"scientific", "editorial"}:
            raise ValueError("mode must be 'scientific' or 'editorial'")
        _nonempty("crs", self.crs)
        if not self.sources:
            raise ValueError("at least one source with provenance is required")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source_id values must be unique")
        for name in ("schema_version", "theme_version"):
            value = getattr(self, name)
            if not value or not all(part.isdigit() for part in value.split(".")):
                raise ValueError(f"{name} must be a numeric dotted version")

    def output_name(self, locale: Locale, extension: OutputFormat) -> str:
        if extension not in self.layout.formats:
            raise ValueError(f"{extension!r} is not enabled by this layout")
        return f"{self.slug}_{locale}.{extension}"
