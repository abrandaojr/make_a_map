"""Locales supported by every final map."""

from typing import Final, Literal

Locale = Literal["pt-BR", "en-US"]
LOCALES: Final[tuple[Locale, Locale]] = ("pt-BR", "en-US")
