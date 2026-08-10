"""Strict bilingual translation catalog and locale-aware formatting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, cast

Locale = Literal["pt-BR", "en-US"]
LOCALES: Final[tuple[Locale, Locale]] = ("pt-BR", "en-US")
TranslationNode: TypeAlias = str | Mapping[str, "TranslationNode"]


def _freeze(node: TranslationNode, path: str = "") -> TranslationNode:
    if isinstance(node, str):
        if not node.strip():
            raise ValueError(f"translation at {path or '<root>'!r} cannot be empty")
        return node
    if not isinstance(node, Mapping):
        raise TypeError(f"translation at {path or '<root>'!r} must be text or a mapping")
    frozen: dict[str, TranslationNode] = {}
    for key, value in node.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"translation key at {path or '<root>'!r} must be a non-empty string")
        child_path = f"{path}.{key}" if path else key
        frozen[key] = _freeze(value, child_path)
    return MappingProxyType(frozen)


def _leaf_paths(node: TranslationNode, prefix: str = "") -> set[str]:
    if isinstance(node, str):
        return {prefix}
    paths: set[str] = set()
    for key, value in node.items():
        paths.update(_leaf_paths(value, f"{prefix}.{key}" if prefix else key))
    return paths


@dataclass(frozen=True, slots=True)
class TranslationCatalog:
    """Exactly two recursively equivalent locale trees."""

    translations: Mapping[Locale, TranslationNode]

    def __post_init__(self) -> None:
        received = set(self.translations)
        required = set(LOCALES)
        if received != required:
            missing = sorted(required - received)
            extra = sorted(received - required)
            raise ValueError(f"locales must be exactly {LOCALES}; missing={missing}, extra={extra}")
        for locale in LOCALES:
            if not isinstance(self.translations[locale], Mapping):
                raise TypeError(f"translation root for {locale} must be a mapping")
        frozen = {locale: _freeze(self.translations[locale], locale) for locale in LOCALES}
        pt_paths = _leaf_paths(frozen["pt-BR"])
        en_paths = _leaf_paths(frozen["en-US"])
        if pt_paths != en_paths:
            only_pt = sorted(pt_paths - en_paths)
            only_en = sorted(en_paths - pt_paths)
            raise ValueError(
                "translation keys must have recursive parity; "
                f"only in pt-BR={only_pt}, only in en-US={only_en}"
            )
        object.__setattr__(self, "translations", MappingProxyType(frozen))

    def get(self, locale: Locale, key: str) -> str:
        if locale not in LOCALES:
            raise ValueError(f"unsupported locale {locale!r}; expected one of {LOCALES}")
        node: TranslationNode = self.translations[locale]
        for part in key.split("."):
            if not isinstance(node, Mapping) or part not in node:
                raise KeyError(f"missing translation {key!r} for {locale}")
            node = node[part]
        if not isinstance(node, str):
            raise KeyError(f"translation {key!r} for {locale} is a group, not text")
        return node


def format_number(value: float | Decimal, locale: Locale, decimals: int = 0) -> str:
    """Format a finite decimal without relying on the host OS locale."""
    if locale not in LOCALES:
        raise ValueError(f"unsupported locale {locale!r}; expected one of {LOCALES}")
    if decimals < 0:
        raise ValueError("decimals must be non-negative")
    number = Decimal(str(value))
    if not number.is_finite():
        raise ValueError("value must be finite")
    rendered = f"{number:,.{decimals}f}"
    if locale == "pt-BR":
        rendered = rendered.translate(str.maketrans({",": ".", ".": ","}))
    return rendered


def require_locale(value: str) -> Locale:
    if value not in LOCALES:
        raise ValueError(f"unsupported locale {value!r}; expected one of {LOCALES}")
    return cast(Locale, value)
