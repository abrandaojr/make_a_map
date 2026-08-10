from copy import deepcopy

import pytest

from make_a_map.recipes import RecipeSpec, RecipeValidationError, list_recipes

EXPECTED_RECIPES = {
    "biome",
    "municipality",
    "neighborhood",
    "rural-property",
    "slaughterhouse-purchasing-zone",
    "legal-amazon-municipalities",
}
SENSITIVE_RECIPES = {"rural-property", "slaughterhouse-purchasing-zone"}


def test_initial_recipe_gallery_is_complete_and_explicitly_preproduction() -> None:
    recipes = list_recipes()

    assert {recipe.slug for recipe in recipes} == EXPECTED_RECIPES
    assert all(recipe.maturity in {"concept", "experimental"} for recipe in recipes)


@pytest.mark.parametrize("locale", ["pt-BR", "en-US"])
def test_every_recipe_has_bilingual_editorial_content(locale: str) -> None:
    for recipe in list_recipes():
        assert recipe.title[locale].strip()  # type: ignore[index]
        assert recipe.description[locale].strip()  # type: ignore[index]
        assert recipe.purpose[locale].strip()  # type: ignore[index]
        assert recipe.question[locale].strip()  # type: ignore[index]
        assert {"map", "globe"}.issubset(recipe.layout["modules"])


def test_sensitive_recipes_require_review_and_defensive_controls() -> None:
    recipes = {recipe.slug: recipe for recipe in list_recipes()}

    for slug in SENSITIVE_RECIPES:
        recipe = recipes[slug]
        controls = set(recipe.privacy["controls"])
        assert recipe.kind == "sensitive"
        assert recipe.human_review_required is True
        assert "human_review" in controls

    assert {
        "coordinate_generalization",
        "strip_identifiers",
        "consent_or_public_interest",
    }.issubset(recipes["rural-property"].privacy["controls"])
    assert {
        "minimum_cell_count",
        "no_supplier_points",
        "legal_and_ethics_review",
    }.issubset(recipes["slaughterhouse-purchasing-zone"].privacy["controls"])


def test_sensitive_recipe_cannot_disable_human_review() -> None:
    source = next(recipe for recipe in list_recipes() if recipe.slug == "rural-property")
    unsafe = deepcopy(source.raw)
    unsafe["human_review_required"] = False

    with pytest.raises(RecipeValidationError, match="require human review"):
        RecipeSpec.from_dict(unsafe)


def test_scaffold_never_marks_review_as_approved() -> None:
    for recipe in list_recipes():
        scaffold = recipe.scaffold()
        assert scaffold["locale_outputs"] == ["pt-BR", "en-US"]
        assert scaffold["human_review"]["approved_by"] is None
        assert scaffold["human_review"]["required"] is recipe.human_review_required
        assert set(scaffold["inputs"]) == {field["name"] for field in recipe.required_fields}
