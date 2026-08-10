"""Source-line component assembled from provenance, never hand-copied URLs."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..data import Provenance


def source_line(locale: str, sources: Iterable[Provenance], crs_label: str) -> str:
    prefix = "Fonte" if locale == "pt-BR" else "Source"
    entries = list(sources)
    publishers = {item.publisher for item in entries}
    publisher = next(iter(publishers)) if len(publishers) == 1 else ""
    acronym = re.search(r"\(([A-Z]{2,})\)", publisher)
    credit = acronym.group(1) if acronym else publisher
    parts = [f"{item.title} ({item.edition})" for item in entries]
    lead = f"{credit} — " if credit else ""
    return f"{prefix}: {lead}{'; '.join(parts)}. CRS: {crs_label}."
