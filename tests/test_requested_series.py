from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

from make_a_map.components.globe import DEFAULT_COLORS
from make_a_map.maps.requested_series import (
    AMAZON_COLOR,
    BIOME_NAMES,
    CERRADO_COLOR,
    CONSERVATION_COLOR,
    CONTEXT,
    CONTEXT_DARK,
    COPY,
    INDIGENOUS_COLOR,
    INK,
    LEGEND_FONT_SIZE,
    MAJOR_CITIES,
    MUNICIPALITY_GEOCODES_PATH,
    OCEAN,
    OSM_ATTRIBUTION,
    PAPER,
    RELIEF_COPY,
    SAO_FELIX_CODE,
    SECOND_THEME,
    SERIES,
    THEME,
    _add_state_labels,
    _figure,
    _regional_world_land,
    _set_square_extent,
    municipality_geocode,
)


def _is_gray(color: str) -> bool:
    red, green, blue = (int(color[index : index + 2], 16) for index in (1, 3, 5))
    return red == green == blue


def test_requested_series_has_six_bilingual_maps() -> None:
    assert len(SERIES) == 6
    assert set(SERIES) == set(COPY)
    assert SAO_FELIX_CODE == "1507300"
    assert SERIES[:4] == (
        "amazon-cerrado-biomes",
        "amazon-biome",
        "cerrado-biome",
        "sao-felix-do-xingu",
    )
    for slug in SERIES:
        assert set(COPY[slug]) == {"pt-BR", "en-US"}
        assert all(title and subtitle for title, subtitle in COPY[slug].values())
    assert set(RELIEF_COPY) == {"pt-BR", "en-US"}
    assert OSM_ATTRIBUTION == "© OpenStreetMap contributors"


def test_official_biome_names_do_not_confuse_cerrado_with_caatinga() -> None:
    biomes = gpd.GeoDataFrame(
        {
            "CD_BIOMA": ["1", "2", "3"],
            "NM_BIOMA": ["Amazônia", "Caatinga", "Cerrado"],
        },
        geometry=[box(-74, -17, -43, 5), box(-45, -17, -35, -3), box(-60, -25, -41, -2)],
        crs="EPSG:4674",
    )

    cerrado = biomes.loc[biomes.NM_BIOMA == BIOME_NAMES["cerrado"]]

    assert cerrado.CD_BIOMA.tolist() == ["3"]
    assert cerrado.NM_BIOMA.tolist() == ["Cerrado"]
    assert cerrado.total_bounds[0] < -55


def test_series_uses_direct_output_folders() -> None:
    output_root = Path("outputs")

    for slug in SERIES:
        assert output_root / slug / "latest" == Path("outputs", slug, "latest")


def test_sao_felix_uses_edition_locked_municipality_catalog() -> None:
    assert MUNICIPALITY_GEOCODES_PATH.is_file()
    assert municipality_geocode("São Félix do Xingu", "PA") == "1507300"


def test_boundary_forward_palette_matches_selected_design_study() -> None:
    assert _is_gray(PAPER)
    assert CONTEXT == "#E1E0DB"
    assert OCEAN == "#CCD3D5"
    assert CONTEXT_DARK == "#87908B"
    assert INK == "#303735"
    assert not _is_gray(THEME)
    assert not _is_gray(SECOND_THEME)
    assert AMAZON_COLOR == "#6F927F"
    assert CERRADO_COLOR == "#D8C39B"
    assert CONSERVATION_COLOR == "#315C4C"
    assert INDIGENOUS_COLOR == "#A56849"
    assert THEME == AMAZON_COLOR
    assert SECOND_THEME == CERRADO_COLOR


def test_locator_globe_is_entirely_grayscale() -> None:
    assert all(_is_gray(color) for color in DEFAULT_COLORS.values())


def test_major_city_priority_starts_with_largest_selected_municipalities() -> None:
    assert MAJOR_CITIES[:3] == (
        ("São Paulo", "SP"),
        ("Rio de Janeiro", "RJ"),
        ("Brasília", "DF"),
    )


def test_map_canvas_is_full_bleed_seven_and_a_half_inches_without_title() -> None:
    figure, axes, overlay = _figure("amazon-biome", "pt-BR")
    try:
        assert tuple(figure.get_size_inches()) == (7.5, 7.5)
        assert tuple(axes.get_position().bounds) == (0.0, 0.0, 1.0, 1.0)
        assert figure.get_facecolor() == axes.get_facecolor()
        assert len(overlay.texts) == 0
        assert LEGEND_FONT_SIZE == 16
    finally:
        plt.close(figure)


def test_square_extent_preserves_complete_geometry_without_side_bands() -> None:
    figure, axes, _ = _figure("cerrado-biome", "pt-BR")
    try:
        _set_square_extent(axes, (10, 20, 30, 70), padding_ratio=0.03)
        assert axes.get_xlim()[1] - axes.get_xlim()[0] == axes.get_ylim()[1] - axes.get_ylim()[0]
        assert axes.get_xlim()[0] < 10
        assert axes.get_xlim()[1] > 30
        assert axes.get_ylim()[0] < 20
        assert axes.get_ylim()[1] > 70
    finally:
        plt.close(figure)


def test_regional_world_land_uses_safe_projection_domain(tmp_path: Path) -> None:
    source = gpd.GeoDataFrame(
        geometry=[box(-180, -80, 180, 80)], crs="EPSG:4326"
    )
    path = tmp_path / "world.gpkg"
    source.to_file(path, driver="GPKG")

    regional = _regional_world_land(path)

    assert regional.crs.to_string() == "EPSG:5880"
    assert regional.to_crs("EPSG:4326").total_bounds[0] >= -100.01
    assert regional.to_crs("EPSG:4326").total_bounds[2] <= -19.99


def test_state_labels_use_official_names_for_visible_units() -> None:
    states = gpd.GeoDataFrame(
        {"NM_UF": ["Pará", "Amazonas"]},
        geometry=[box(0, 0, 10, 10), box(10, 0, 20, 10)],
        crs="EPSG:5880",
    )
    figure, axes, _ = _figure("amazon-biome", "pt-BR")
    try:
        axes.set_xlim(0, 20)
        axes.set_ylim(0, 20)
        _add_state_labels(axes, states, local=False)
        assert {text.get_text() for text in axes.texts} == {"PARÁ", "AMAZONAS"}
    finally:
        plt.close(figure)
