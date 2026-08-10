"""Reusable, bilingual editorial cartography for Brazil."""

from .contracts import (
    LayoutSpec,
    MapSpec,
    Quantity,
    SourceSpec,
    Statistic,
)
from .i18n import LOCALES, TranslationCatalog
from .theme import DEFAULT_THEME, Theme

__all__ = [
    "DEFAULT_THEME",
    "LOCALES",
    "LayoutSpec",
    "MapSpec",
    "Quantity",
    "SourceSpec",
    "Statistic",
    "Theme",
    "TranslationCatalog",
]

__version__ = "0.1.0"
