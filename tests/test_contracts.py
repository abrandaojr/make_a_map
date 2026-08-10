from datetime import date

import pytest

from make_a_map.contracts import LayoutSpec, MapSpec, SourceSpec
from make_a_map.i18n import TranslationCatalog


def catalog() -> TranslationCatalog:
    return TranslationCatalog({"pt-BR": {"title": "Mapa"}, "en-US": {"title": "Map"}})


def source() -> SourceSpec:
    return SourceSpec(
        source_id="ibge-test",
        publisher="IBGE",
        product="Malha sintética",
        edition="2024",
        url="https://example.invalid/ibge.zip",
        accessed=date(2026, 8, 10),
        original_crs="EPSG:4674",
        sha256="a" * 64,
    )


@pytest.mark.parametrize(("dpi", "pixels"), [(300, (2250, 2250)), (600, (4500, 4500))])
def test_layout_has_fixed_square_publication_size(dpi: int, pixels: tuple[int, int]) -> None:
    layout = LayoutSpec(dpi=dpi)

    assert (layout.width_inches, layout.height_inches) == (7.5, 7.5)
    assert layout.pixel_size == pixels
    assert layout.globe_inset is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width_inches": 8},
        {"height_inches": 8},
        {"dpi": 150},
        {"globe_inset": False},
        {"formats": ("png", "png")},
    ],
)
def test_layout_rejects_contract_drift(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        LayoutSpec(**kwargs)


def test_output_names_are_predictable_and_bilingual() -> None:
    spec = MapSpec(
        slug="mapa-sintetico",
        mode="scientific",
        crs="EPSG:5880",
        catalog=catalog(),
        sources=(source(),),
    )

    assert spec.output_name("pt-BR", "png") == "mapa-sintetico_pt-BR.png"
    assert spec.output_name("en-US", "svg") == "mapa-sintetico_en-US.svg"


def test_map_requires_versioned_provenance() -> None:
    with pytest.raises(ValueError, match="at least one source"):
        MapSpec(
            slug="sem-fonte",
            mode="scientific",
            crs="EPSG:5880",
            catalog=catalog(),
            sources=(),
        )
