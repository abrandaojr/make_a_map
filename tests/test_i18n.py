from decimal import Decimal

import pytest

from make_a_map.contracts import Quantity, Statistic
from make_a_map.i18n import TranslationCatalog, format_number


def test_catalog_requires_recursive_key_parity() -> None:
    with pytest.raises(ValueError, match="recursive parity"):
        TranslationCatalog(
            {
                "pt-BR": {"map": {"title": "Amazônia", "note": "Nota"}},
                "en-US": {"map": {"title": "Amazon"}},
            }
        )


def test_catalog_requires_exactly_two_supported_locales() -> None:
    with pytest.raises(ValueError, match="locales must be exactly"):
        TranslationCatalog({"pt-BR": {"title": "Mapa"}})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("locale", "expected"),
    [("pt-BR", "1.234.567,89"), ("en-US", "1,234,567.89")],
)
def test_number_formatting_is_locale_aware(locale: str, expected: str) -> None:
    assert format_number(Decimal("1234567.89"), locale, 2) == expected  # type: ignore[arg-type]


def test_typed_statistic_translates_unit_and_label() -> None:
    catalog = TranslationCatalog(
        {
            "pt-BR": {"stat": {"area": "Área"}, "unit": {"km2": "km²"}},
            "en-US": {"stat": {"area": "Area"}, "unit": {"km2": "km²"}},
        }
    )
    statistic = Statistic("stat.area", Quantity(5001234.5, "unit.km2", decimals=1))

    assert statistic.format("pt-BR", catalog) == ("Área", "5.001.234,5 km²", None)
    assert statistic.format("en-US", catalog) == ("Area", "5,001,234.5 km²", None)


def test_quantity_with_unit_cannot_be_rendered_without_catalog() -> None:
    with pytest.raises(ValueError, match="translation catalog"):
        Quantity(10, "unit.km2").format("pt-BR")
