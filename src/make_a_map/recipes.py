"""Versioned, data-only recipes for common Brazilian map assignments.

Recipes describe editorial intent and evidence requirements.  They deliberately do
not render maps: a renderer consumes a validated :class:`RecipeSpec` later.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Maturity = Literal["concept", "experimental", "validated", "production"]
Kind = Literal["locator", "thematic", "sensitive"]

SCHEMA_VERSION = "1.0"
MATURITIES = frozenset({"concept", "experimental", "validated", "production"})
KINDS = frozenset({"locator", "thematic", "sensitive"})
LAYOUT_MODULES = frozenset(
    {
        "title",
        "subtitle",
        "map",
        "legend",
        "annotations",
        "scale",
        "north_arrow",
        "globe",
        "notes",
        "sources",
    }
)
_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECIPE_DIR = _PACKAGE_ROOT / "recipes"


class RecipeValidationError(ValueError):
    """Raised when a recipe does not satisfy the public recipe contract."""


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RecipeValidationError(f"{path} must be an object")
    return value


def _required(obj: Mapping[str, Any], names: set[str], path: str) -> None:
    missing = names - set(obj)
    if missing:
        raise RecipeValidationError(f"{path} is missing: {', '.join(sorted(missing))}")


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RecipeValidationError(f"{path} must be a non-empty string")
    return value.strip()


def _bilingual(value: Any, path: str) -> dict[str, str]:
    obj = _object(value, path)
    _required(obj, {"pt-BR", "en-US"}, path)
    if set(obj) != {"pt-BR", "en-US"}:
        raise RecipeValidationError(f"{path} must contain exactly pt-BR and en-US")
    return {locale: _text(obj[locale], f"{path}.{locale}") for locale in ("pt-BR", "en-US")}


@dataclass(frozen=True, slots=True)
class RecipeSpec:
    """A validated recipe, retaining its complete JSON-compatible definition."""

    slug: str
    schema_version: str
    recipe_version: str
    maturity: Maturity
    kind: Kind
    title: Mapping[str, str]
    description: Mapping[str, str]
    purpose: Mapping[str, str]
    question: Mapping[str, str]
    layout: Mapping[str, Any]
    required_fields: tuple[Mapping[str, Any], ...]
    source: Mapping[str, Any]
    crs: Mapping[str, Any]
    method: Mapping[str, Any]
    privacy: Mapping[str, Any]
    classification: Mapping[str, Any]
    human_review_required: bool
    raw: Mapping[str, Any]

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> RecipeSpec:
        data = _object(value, "recipe")
        required = {
            "schema_version",
            "recipe_version",
            "slug",
            "maturity",
            "kind",
            "title",
            "description",
            "purpose",
            "question",
            "layout",
            "required_fields",
            "source",
            "crs",
            "method",
            "privacy",
            "classification",
            "human_review_required",
        }
        _required(data, required, "recipe")
        schema_version = _text(data["schema_version"], "schema_version")
        if schema_version != SCHEMA_VERSION:
            raise RecipeValidationError(
                f"unsupported schema_version {schema_version!r}; expected {SCHEMA_VERSION!r}"
            )
        recipe_version = _text(data["recipe_version"], "recipe_version")
        if not re.fullmatch(r"\d+\.\d+\.\d+", recipe_version):
            raise RecipeValidationError("recipe_version must use MAJOR.MINOR.PATCH")
        slug = _text(data["slug"], "slug")
        if not _SLUG.fullmatch(slug):
            raise RecipeValidationError("slug must be lowercase kebab-case")
        maturity = data["maturity"]
        kind = data["kind"]
        if maturity not in MATURITIES:
            raise RecipeValidationError(f"invalid maturity: {maturity!r}")
        if kind not in KINDS:
            raise RecipeValidationError(f"invalid kind: {kind!r}")

        layout = _object(data["layout"], "layout")
        _required(layout, {"grammar", "modules"}, "layout")
        _text(layout["grammar"], "layout.grammar")
        modules = layout["modules"]
        if not isinstance(modules, list) or not modules:
            raise RecipeValidationError("layout.modules must be a non-empty list")
        unknown_modules = set(modules) - LAYOUT_MODULES
        if unknown_modules:
            raise RecipeValidationError(f"unknown layout modules: {sorted(unknown_modules)}")
        if "map" not in modules or "globe" not in modules:
            raise RecipeValidationError("layout.modules must include map and globe")

        fields = data["required_fields"]
        if not isinstance(fields, list) or not fields:
            raise RecipeValidationError("required_fields must be a non-empty list")
        field_names: list[str] = []
        for index, field in enumerate(fields):
            item = _object(field, f"required_fields[{index}]")
            _required(item, {"name", "type", "description"}, f"required_fields[{index}]")
            field_names.append(_text(item["name"], f"required_fields[{index}].name"))
            _text(item["type"], f"required_fields[{index}].type")
            _bilingual(item["description"], f"required_fields[{index}].description")
        if len(field_names) != len(set(field_names)):
            raise RecipeValidationError("required field names must be unique")

        source = _object(data["source"], "source")
        crs = _object(data["crs"], "crs")
        method = _object(data["method"], "method")
        privacy = _object(data["privacy"], "privacy")
        classification = _object(data["classification"], "classification")
        _required(source, {"preferred", "provenance_required"}, "source")
        _required(crs, {"selection_rule", "declare_output_crs"}, "crs")
        _required(method, {"summary", "qa"}, "method")
        _required(privacy, {"risk", "controls"}, "privacy")
        _required(classification, {"strategy", "legend_required"}, "classification")
        _bilingual(source["preferred"], "source.preferred")
        _bilingual(crs["selection_rule"], "crs.selection_rule")
        _bilingual(method["summary"], "method.summary")
        _bilingual(privacy["risk"], "privacy.risk")
        _bilingual(classification["strategy"], "classification.strategy")
        review = data["human_review_required"]
        if not isinstance(review, bool):
            raise RecipeValidationError("human_review_required must be boolean")
        if kind == "sensitive" and not review:
            raise RecipeValidationError("sensitive recipes require human review")

        return cls(
            slug=slug,
            schema_version=schema_version,
            recipe_version=recipe_version,
            maturity=maturity,
            kind=kind,
            title=_bilingual(data["title"], "title"),
            description=_bilingual(data["description"], "description"),
            purpose=_bilingual(data["purpose"], "purpose"),
            question=_bilingual(data["question"], "question"),
            layout=dict(layout),
            required_fields=tuple(dict(field) for field in fields),
            source=dict(source),
            crs=dict(crs),
            method=dict(method),
            privacy=dict(privacy),
            classification=dict(classification),
            human_review_required=review,
            raw=dict(data),
        )

    def scaffold(self) -> dict[str, Any]:
        """Return a CLI-friendly assignment skeleton without mutating the recipe."""
        return {
            "recipe": self.slug,
            "recipe_version": self.recipe_version,
            "locale_outputs": ["pt-BR", "en-US"],
            "inputs": {field["name"]: None for field in self.required_fields},
            "human_review": {"required": self.human_review_required, "approved_by": None},
        }


def load_recipe(slug_or_path: str | Path, recipe_dir: str | Path | None = None) -> RecipeSpec:
    """Load a recipe by slug or JSON path and validate it."""
    candidate = Path(slug_or_path)
    if not candidate.exists():
        candidate = Path(recipe_dir or DEFAULT_RECIPE_DIR) / f"{slug_or_path}.json"
    if not candidate.is_file():
        raise FileNotFoundError(f"recipe not found: {slug_or_path}")
    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise RecipeValidationError(f"invalid JSON in {candidate}: {error}") from error
    recipe = RecipeSpec.from_dict(payload)
    if candidate.stem != recipe.slug:
        raise RecipeValidationError(
            f"filename {candidate.stem!r} does not match slug {recipe.slug!r}"
        )
    return recipe


def list_recipes(recipe_dir: str | Path | None = None) -> tuple[RecipeSpec, ...]:
    """Return every valid catalog entry, sorted by slug (convenient for CLI output)."""
    directory = Path(recipe_dir or DEFAULT_RECIPE_DIR)
    return tuple(load_recipe(path) for path in sorted(directory.glob("*.json")))


def scaffold_recipe(slug: str, recipe_dir: str | Path | None = None) -> dict[str, Any]:
    """Load ``slug`` and return its assignment scaffold."""
    return load_recipe(slug, recipe_dir).scaffold()
