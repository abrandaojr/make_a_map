"""Build the six-map Amazon, Cerrado, and Sao Felix do Xingu series."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject
from shapely import affinity
from shapely.geometry import box

from ..components.globe import add_globe_inset
from ..data import Provenance, fetch_source
from ..export import atomic_output, file_hash, promote_output
from ..i18n import LOCALES, Locale

ROOT = Path(__file__).resolve().parents[3]
DISPLAY_CRS = "EPSG:5880"
MUNICIPALITY_GEOCODES_PATH = ROOT / "data" / "catalog" / "municipalities.json"
# Boundary-forward palette selected from design study 08. Muted thematic fills
# let the dark outlines carry the hierarchy without using pure black.
AMAZON_COLOR = "#6F927F"
CERRADO_COLOR = "#D8C39B"
CONSERVATION_COLOR = "#315C4C"
INDIGENOUS_COLOR = "#A56849"
THEME = AMAZON_COLOR
SECOND_THEME = CERRADO_COLOR
INK = "#303735"
PAPER = "#F2F2F2"
CONTEXT = "#E1E0DB"
OCEAN = "#CCD3D5"
CONTEXT_DARK = "#87908B"
MUTED_INK = "#4B5350"
LEGEND_FONT_SIZE = 16
RELIEF_ALPHA_NATIONAL = 0.10
RELIEF_ALPHA_LOCAL = 0.10
RELIEF_SOURCE_ID = "natural_earth_shaded_relief_50m_3_2_0"
RELIEF_COPY = {
    "pt-BR": "Relevo sombreado suave derivado do SRTM Plus.",
    "en-US": "Subtle shaded relief derived from SRTM Plus.",
}
OSM_ATTRIBUTION = "© OpenStreetMap contributors"

SERIES = (
    "amazon-cerrado-biomes",
    "amazon-biome",
    "cerrado-biome",
    "sao-felix-do-xingu",
    "sao-felix-do-xingu-car-property",
    "sao-felix-do-xingu-purchasing-zone",
)

COPY = {
    "amazon-biome": {
        "pt-BR": ("Bioma Amazônia", "Limite oficial do IBGE · 2025"),
        "en-US": ("Amazon biome", "Official IBGE boundary · 2025"),
    },
    "cerrado-biome": {
        "pt-BR": ("Bioma Cerrado", "Limite oficial do IBGE · 2025"),
        "en-US": ("Cerrado biome", "Official IBGE boundary · 2025"),
    },
    "amazon-cerrado-biomes": {
        "pt-BR": ("Amazônia e Cerrado", "Limites oficiais do IBGE · 2025"),
        "en-US": ("Amazon and Cerrado", "Official IBGE boundaries · 2025"),
    },
    "sao-felix-do-xingu": {
        "pt-BR": ("São Félix do Xingu", "Município do Pará · áreas protegidas e entorno"),
        "en-US": ("Sao Felix do Xingu", "Municipality in Para · protected areas and surroundings"),
    },
    "sao-felix-do-xingu-car-property": {
        "pt-BR": ("Imóvel rural em São Félix do Xingu", "Exemplo CAR sintético · sem proprietário ou código"),
        "en-US": ("Rural property in Sao Felix do Xingu", "Synthetic CAR example · no owner or registry code"),
    },
    "sao-felix-do-xingu-purchasing-zone": {
        "pt-BR": ("Zona de compra em São Félix do Xingu", "Zona sintética de 40 km · sem fornecedores"),
        "en-US": ("Purchasing zone in Sao Felix do Xingu", "Synthetic 40 km zone · no suppliers"),
    },
}

BIOME_NAMES = {
    "amazon": "Amazônia",
    "cerrado": "Cerrado",
}

MAJOR_CITIES = (
    ("São Paulo", "SP"),
    ("Rio de Janeiro", "RJ"),
    ("Brasília", "DF"),
    ("Fortaleza", "CE"),
    ("Salvador", "BA"),
    ("Belo Horizonte", "MG"),
    ("Manaus", "AM"),
    ("Curitiba", "PR"),
    ("Recife", "PE"),
    ("Goiânia", "GO"),
    ("Belém", "PA"),
    ("Porto Alegre", "RS"),
    ("Guarulhos", "SP"),
    ("Campinas", "SP"),
    ("São Gonçalo", "RJ"),
)


def municipality_geocode(name: str, state: str) -> str:
    """Resolve one municipality against the edition-locked IBGE JSON catalog."""
    payload = json.loads(MUNICIPALITY_GEOCODES_PATH.read_text(encoding="utf-8"))
    matches = [
        item["geocode"]
        for item in payload["municipalities"]
        if item["name"] == name and item["state"] == state
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one municipality named {name!r} in {state}, found {len(matches)}")
    return str(matches[0])


SAO_FELIX_CODE = municipality_geocode("São Félix do Xingu", "PA")


def _osm_context(path: Path, bounds: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    """Load scale-appropriate OSM linework, caching only the derived spatial subset."""
    derived = path.parent / "sao_felix_context.gpkg"
    if not derived.exists():
        context = gpd.read_file(
            path,
            layer="lines",
            bbox=bounds,
            where="highway IN ('primary','secondary','tertiary') OR waterway = 'river'",
            columns=["osm_id", "name", "highway", "waterway", "geometry"],
        )
        context.to_file(derived, layer="context", driver="GPKG")
    return gpd.read_file(derived, layer="context").to_crs(DISPLAY_CRS)


def _regional_world_land(path: Path) -> gpd.GeoDataFrame:
    """Clip global land before projection to prevent out-of-domain wrap artifacts."""
    world = gpd.read_file(path)
    south_america_context = box(-100, -60, -20, 20)
    return world.clip(south_america_context).to_crs(DISPLAY_CRS)


def _load(offline: bool) -> tuple[dict[str, gpd.GeoDataFrame], list[Provenance]]:
    ids = {
        "states": "ibge_federation_units_2024",
        "municipalities": "ibge_municipalities_2024",
        "biomes": "ibge_biomes_2025",
        "localities": "ibge_localities_2022",
        "conservation_units": "mma_cnuc_2025_08",
        "indigenous_lands": "funai_indigenous_lands_2026_08_11",
        "osm": "openstreetmap_norte_2026_08_09",
        "world": "natural_earth_admin_0_countries_5_1_2",
        "relief": RELIEF_SOURCE_ID,
    }
    fetched = {name: fetch_source(source_id, offline=offline) for name, source_id in ids.items()}
    states_wgs = gpd.read_file(fetched["states"][0])
    municipalities_wgs = gpd.read_file(
        fetched["municipalities"][0],
        where=f"CD_MUN = '{SAO_FELIX_CODE}'",
    )
    if len(municipalities_wgs) != 1:
        raise ValueError(
            f"expected exactly one Sao Felix do Xingu feature, found {len(municipalities_wgs)}"
        )
    sao_felix = municipalities_wgs.to_crs(DISPLAY_CRS)
    municipality_bounds = tuple(municipalities_wgs.total_bounds)
    neighbors = gpd.read_file(
        fetched["municipalities"][0],
        bbox=municipality_bounds,
        columns=["CD_MUN", "NM_MUN", "geometry"],
    ).to_crs(DISPLAY_CRS)
    city_codes = [municipality_geocode(name, state) for name, state in MAJOR_CITIES]
    city_candidates = gpd.read_file(
        fetched["localities"][0],
        columns=[
            "CD_MUN",
            "NM_MUN",
            "SIGLA_UF",
            "CT_LOCALID",
            "SCT_LOCALI",
            "NM_LOCALID",
            "geometry",
        ],
    )
    city_candidates = city_candidates.loc[
        city_candidates.CD_MUN.isin(city_codes) & (city_candidates.CT_LOCALID == "Cidade")
    ]
    selected_cities = []
    rank_by_code = {code: rank for rank, code in enumerate(city_codes)}
    for code in city_codes:
        candidates = city_candidates.loc[city_candidates.CD_MUN == code].copy()
        capital = candidates.loc[candidates.SCT_LOCALI.str.startswith("Capital", na=False)]
        selected = capital if not capital.empty else candidates.loc[candidates.SCT_LOCALI == "Sede Municipal"]
        if len(selected) != 1:
            raise ValueError(f"expected one official IBGE capital or municipal seat for {code}")
        selected_cities.append(selected.iloc[0])
    cities = gpd.GeoDataFrame(selected_cities, crs=city_candidates.crs).to_crs(DISPLAY_CRS)
    cities["POP_RANK"] = cities.CD_MUN.map(rank_by_code)
    cities = cities.sort_values("POP_RANK")
    if len(cities) != len(MAJOR_CITIES):
        raise ValueError(f"expected {len(MAJOR_CITIES)} major cities, found {len(cities)}")
    biomes = gpd.read_file(fetched["biomes"][0]).to_crs(DISPLAY_CRS)
    conservation_units = gpd.read_file(
        fetched["conservation_units"][0],
        bbox=municipality_bounds,
        columns=["nome_uc", "geometry"],
    ).to_crs(DISPLAY_CRS)
    indigenous_lands = gpd.read_file(
        fetched["indigenous_lands"][0],
        bbox=municipality_bounds,
        columns=["terrai_nom", "geometry"],
    ).to_crs(DISPLAY_CRS)
    return (
        {
            "states": states_wgs.to_crs(DISPLAY_CRS),
            "states_wgs": gpd.GeoDataFrame(
                geometry=[states_wgs.geometry.union_all().simplify(0.08, preserve_topology=True)],
                crs=states_wgs.crs,
            ),
            "world": gpd.read_file(fetched["world"][0]).assign(
                geometry=lambda frame: frame.geometry.simplify(0.08, preserve_topology=True)
            ),
            "world_display": _regional_world_land(fetched["world"][0]),
            "biomes": biomes,
            "sao_felix": sao_felix,
            "neighbors": neighbors,
            "cities": cities,
            "conservation_units": conservation_units,
            "indigenous_lands": indigenous_lands,
            "osm": _osm_context(fetched["osm"][0], municipality_bounds),
            "relief": fetched["relief"][0],
        },
        [value[1] for value in fetched.values()],
    )


def _figure(slug: str, locale: Locale) -> tuple[plt.Figure, plt.Axes, plt.Axes]:
    # A continuous neutral field reaches every edge; geographic aspect must
    # never shrink the full-bleed axes and expose paper-colored side bands.
    background = OCEAN
    figure = plt.figure(figsize=(7.5, 7.5), facecolor=background)
    axes = figure.add_axes((0.0, 0.0, 1.0, 1.0), facecolor=background)
    overlay = figure.add_axes((0.0, 0.0, 1.0, 1.0), facecolor="none", zorder=200)
    overlay.set_axis_off()
    axes.set_axis_off()
    return figure, axes, overlay


def _legend(
    figure: plt.Figure,
    labels: list[str],
    colors: list[str],
    *,
    line_labels: list[str] | None = None,
) -> None:
    handles: list[Patch | Line2D] = [
        Patch(facecolor=color, edgecolor=INK, linewidth=0.45) for color in colors
    ]
    line_labels = line_labels or []
    handles.extend(
        Line2D([0], [0], color=INK, linewidth=1.2, linestyle=(0, (2, 1)))
        for _ in line_labels
    )
    legend = figure.legend(
        handles,
        [*labels, *line_labels],
        loc="lower left",
        bbox_to_anchor=(0.022, 0.025),
        frameon=True,
        fancybox=False,
        framealpha=0.72,
        facecolor=PAPER,
        edgecolor="none",
        fontsize=LEGEND_FONT_SIZE,
        labelcolor=INK,
    )
    legend.get_frame().set_linewidth(0)


def _synthetic_property(municipality: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = municipality.total_bounds
    center = municipality.geometry.union_all().representative_point()
    width = (maxx - minx) * 0.13
    height = (maxy - miny) * 0.10
    geometry = affinity.rotate(
        box(center.x - width / 2, center.y - height / 2, center.x + width / 2, center.y + height / 2),
        12,
        origin="center",
    ).intersection(municipality.geometry.union_all())
    return gpd.GeoDataFrame(geometry=[geometry], crs=municipality.crs)


def _set_square_extent(
    axes: plt.Axes,
    bounds: tuple[float, float, float, float] | list[float],
    *,
    padding_ratio: float,
) -> None:
    """Fill a square canvas without distorting or clipping the mapped extent."""
    minx, miny, maxx, maxy = bounds
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2
    span = max(maxx - minx, maxy - miny) * (1 + 2 * padding_ratio)
    axes.set_xlim(center_x - span / 2, center_x + span / 2)
    axes.set_ylim(center_y - span / 2, center_y + span / 2)


def _add_relief(axes: plt.Axes, path: Path, *, alpha: float) -> None:
    """Reproject a subtle, neutral shaded-relief backdrop to the exact map view."""
    x_limits = axes.get_xlim()
    y_limits = axes.get_ylim()
    width = 1500
    destination = np.empty((width, width), dtype=np.uint8)
    with rasterio.open(path) as source:
        reproject(
            source=rasterio.band(source, 1),
            destination=destination,
            src_transform=source.transform,
            src_crs=source.crs or "EPSG:4326",
            dst_transform=from_bounds(
                x_limits[0], y_limits[0], x_limits[1], y_limits[1], width, width
            ),
            dst_crs=DISPLAY_CRS,
            resampling=Resampling.bilinear,
        )
    axes.imshow(
        destination,
        extent=(*x_limits, *y_limits),
        origin="upper",
        cmap="gray",
        vmin=30,
        vmax=235,
        alpha=alpha,
        interpolation="bilinear",
        zorder=2,
    )
    axes.set_xlim(x_limits)
    axes.set_ylim(y_limits)


def _add_state_labels(axes: plt.Axes, states: gpd.GeoDataFrame, *, local: bool) -> None:
    """Label each federation unit by the representative point of its visible portion."""
    x_limits = axes.get_xlim()
    y_limits = axes.get_ylim()
    view = box(x_limits[0], y_limits[0], x_limits[1], y_limits[1])
    visible = states.copy()
    visible["visible_geometry"] = visible.geometry.intersection(view)
    visible = visible.loc[~visible.visible_geometry.is_empty].copy()
    minimum_area = view.area * (0.05 if local else 0.00025)
    visible = visible.loc[visible.visible_geometry.area >= minimum_area]
    for state in visible.itertuples():
        point = state.visible_geometry.representative_point()
        label = axes.annotate(
            state.NM_UF.upper(),
            (point.x, point.y),
            ha="center",
            va="center",
            fontsize=6.4 if local else 5.0,
            color=MUTED_INK,
            family="DejaVu Sans",
            weight="normal",
            zorder=110,
        )
        label.set_path_effects([path_effects.withStroke(linewidth=1.8, foreground=PAPER)])


def _render(
    slug: str,
    locale: Locale,
    layers: dict[str, gpd.GeoDataFrame],
    target: Path,
) -> dict[str, object]:
    figure, axes, _overlay = _figure(slug, locale)
    focus: gpd.GeoDataFrame | None = None
    visible_cities: gpd.GeoDataFrame | None = None
    synthetic = False
    if slug in {"amazon-biome", "cerrado-biome", "amazon-cerrado-biomes"}:
        amazon = layers["biomes"].loc[
            layers["biomes"].NM_BIOMA == BIOME_NAMES["amazon"]
        ]
        cerrado = layers["biomes"].loc[
            layers["biomes"].NM_BIOMA == BIOME_NAMES["cerrado"]
        ]
        if len(amazon) != 1 or len(cerrado) != 1:
            raise ValueError("expected exactly one official Amazon and Cerrado biome feature")
        layers["world_display"].plot(
            ax=axes, color=CONTEXT, edgecolor="none", linewidth=0, zorder=1
        )
        layers["states"].plot(ax=axes, color=CONTEXT, edgecolor=PAPER, linewidth=0.3, zorder=3)
        if slug == "amazon-biome":
            amazon.boundary.plot(ax=axes, color=PAPER, linewidth=2.8, zorder=8)
            amazon.plot(ax=axes, color=AMAZON_COLOR, alpha=0.72, edgecolor=INK, linewidth=1.55, zorder=10)
            focus = amazon
            _legend(
                figure,
                ["Bioma Amazônia" if locale == "pt-BR" else "Amazon biome"],
                [AMAZON_COLOR],
            )
        elif slug == "cerrado-biome":
            cerrado.boundary.plot(ax=axes, color=PAPER, linewidth=2.8, zorder=8)
            cerrado.plot(ax=axes, color=CERRADO_COLOR, alpha=0.72, edgecolor=INK, linewidth=1.55, zorder=10)
            focus = cerrado
            _legend(
                figure,
                ["Bioma Cerrado" if locale == "pt-BR" else "Cerrado biome"],
                [CERRADO_COLOR],
            )
        else:
            focus = gpd.GeoDataFrame(
                geometry=[amazon.geometry.union_all().union(cerrado.geometry.union_all())],
                crs=amazon.crs,
            )
            focus.boundary.plot(ax=axes, color=PAPER, linewidth=2.8, zorder=8)
            amazon.plot(ax=axes, color=AMAZON_COLOR, alpha=0.72, edgecolor=INK, linewidth=1.55, zorder=10)
            cerrado.plot(ax=axes, color=CERRADO_COLOR, alpha=0.72, edgecolor=INK, linewidth=1.55, zorder=10)
            _legend(
                figure,
                ["Amazônia" if locale == "pt-BR" else "Amazon", "Cerrado"],
                [AMAZON_COLOR, CERRADO_COLOR],
            )
        if focus is None:
            raise RuntimeError("biome focus geometry was not prepared")
        _set_square_extent(axes, list(layers["states"].total_bounds), padding_ratio=0.03)
        _add_relief(axes, layers["relief"], alpha=RELIEF_ALPHA_NATIONAL)
        x_limits = axes.get_xlim()
        y_limits = axes.get_ylim()
        visible_cities = layers["cities"].cx[
            x_limits[0] : x_limits[1],
            y_limits[0] : y_limits[1],
        ]
        accepted_indexes = []
        accepted_points = []
        minimum_distance = (x_limits[1] - x_limits[0]) * 0.055
        for city in visible_cities.sort_values("POP_RANK").itertuples():
            if any(city.geometry.distance(point) < minimum_distance for point in accepted_points):
                continue
            accepted_indexes.append(city.Index)
            accepted_points.append(city.geometry)
        visible_cities = visible_cities.loc[accepted_indexes]
        visible_cities.plot(
            ax=axes,
            color=MUTED_INK,
            edgecolor=PAPER,
            linewidth=0.55,
            markersize=18,
            zorder=80,
        )
    else:
        municipality = layers["sao_felix"]
        focus = municipality
        layers["neighbors"].plot(ax=axes, color=CONTEXT, edgecolor=PAPER, linewidth=0.35, zorder=1)
        municipality.plot(ax=axes, color=CONTEXT_DARK, alpha=0.88, edgecolor=INK, linewidth=0.9, zorder=3)
        osm = layers["osm"].clip(municipality.geometry.union_all())
        rivers = osm.loc[osm.waterway == "river"]
        major_roads = osm.loc[osm.highway.isin(["primary", "secondary"])]
        local_roads = osm.loc[osm.highway == "tertiary"]
        rivers.plot(ax=axes, color="#B8B8B8", linewidth=0.6, zorder=65)
        major_roads.plot(
            ax=axes,
            color="#E8E8E8",
            linewidth=0.65,
            linestyle=(0, (5, 3)),
            zorder=70,
        )
        if slug == "sao-felix-do-xingu":
            municipality.boundary.plot(ax=axes, color=PAPER, linewidth=2.8, zorder=8)
            municipality.plot(
                ax=axes,
                color="#A6A6A3",
                edgecolor=INK,
                linewidth=1.55,
                zorder=10,
            )
            rivers.plot(ax=axes, color="#B8B8B8", linewidth=0.6, zorder=65)
            major_roads.plot(
                ax=axes,
                color="#E8E8E8",
                linewidth=0.65,
                linestyle=(0, (5, 3)),
                zorder=70,
            )
            protected_layers = (
                (layers["conservation_units"], CONSERVATION_COLOR),
                (layers["indigenous_lands"], INDIGENOUS_COLOR),
            )
            for protected, color in protected_layers:
                clipped = protected.clip(municipality.geometry.union_all())
                clipped.plot(ax=axes, color=color, alpha=0.72, edgecolor="none", zorder=35)
                clipped.boundary.plot(
                    ax=axes,
                    color=PAPER,
                    linewidth=1.25,
                    linestyle="solid",
                    zorder=75,
                )
            _legend(
                figure,
                [
                    "Unidades de conservação"
                    if locale == "pt-BR"
                    else "Conservation units",
                    "Terras indígenas" if locale == "pt-BR" else "Indigenous lands",
                ],
                [CONSERVATION_COLOR, INDIGENOUS_COLOR],
            )
        elif slug == "sao-felix-do-xingu-car-property":
            property_frame = _synthetic_property(municipality)
            local_roads.plot(
                ax=axes,
                color="#E2E2E2",
                linewidth=0.38,
                linestyle=(0, (1.5, 2.5)),
                zorder=72,
            )
            property_frame.boundary.plot(ax=axes, color=PAPER, linewidth=3.0, zorder=27)
            property_frame.plot(
                ax=axes, color=THEME, alpha=0.72, edgecolor=INK, linewidth=1.55, zorder=28
            )
            focus_geometry = property_frame.geometry.union_all()
            detail_padding = max(
                focus_geometry.bounds[2] - focus_geometry.bounds[0],
                focus_geometry.bounds[3] - focus_geometry.bounds[1],
            ) * 1.7
            detail_bounds = focus_geometry.buffer(detail_padding).bounds
            synthetic = True
            _legend(
                figure,
                ["Imóvel sintético" if locale == "pt-BR" else "Synthetic property"],
                [THEME],
            )
        else:
            center = municipality.geometry.union_all().representative_point()
            zone = gpd.GeoDataFrame(
                geometry=[center.buffer(40_000).intersection(municipality.geometry.union_all())],
                crs=municipality.crs,
            )
            zone.boundary.plot(ax=axes, color=PAPER, linewidth=3.0, zorder=27)
            zone.plot(
                ax=axes, color=THEME, alpha=0.72, edgecolor=INK, linewidth=1.55, zorder=28
            )
            local_roads.plot(
                ax=axes,
                color="#E2E2E2",
                linewidth=0.38,
                linestyle=(0, (1.5, 2.5)),
                zorder=72,
            )
            detail_bounds = zone.geometry.union_all().buffer(32_000).bounds
            synthetic = True
            _legend(
                figure,
                ["Zona sintética de 40 km" if locale == "pt-BR" else "Synthetic 40 km zone"],
                [THEME],
            )

        if slug == "sao-felix-do-xingu":
            _set_square_extent(axes, list(municipality.total_bounds), padding_ratio=0.012)
        else:
            _set_square_extent(axes, detail_bounds, padding_ratio=0)
        _add_relief(axes, layers["relief"], alpha=RELIEF_ALPHA_LOCAL)
        layers["neighbors"].boundary.plot(
            ax=axes, color=PAPER, linewidth=0.42, zorder=84
        )
        municipality.boundary.plot(ax=axes, color=INK, linewidth=1.35, zorder=90)

    # Administrative boundaries are the final map layer and must remain visible
    # over every thematic fill. Restore the existing view because the complete
    # national states layer would otherwise reset the extent of local maps.
    x_limits = axes.get_xlim()
    y_limits = axes.get_ylim()
    layers["states"].boundary.plot(ax=axes, color=INK, linewidth=0.48, zorder=100)
    axes.set_xlim(x_limits)
    axes.set_ylim(y_limits)
    _add_state_labels(
        axes,
        layers["states"],
        local=slug not in {"amazon-biome", "cerrado-biome", "amazon-cerrado-biomes"},
    )
    if slug == "sao-felix-do-xingu":
        view = box(x_limits[0], y_limits[0], x_limits[1], y_limits[1])
        neighboring_labels = layers["neighbors"].loc[
            layers["neighbors"].CD_MUN != SAO_FELIX_CODE
        ].copy()
        neighboring_labels["visible_geometry"] = neighboring_labels.geometry.intersection(view)
        neighboring_labels = neighboring_labels.loc[
            ~neighboring_labels.visible_geometry.is_empty
        ].copy()
        neighboring_labels["visible_area"] = neighboring_labels.visible_geometry.area
        neighboring_labels = neighboring_labels.nlargest(8, "visible_area")
        for neighbor in neighboring_labels.itertuples():
            point = neighbor.visible_geometry.representative_point()
            label = axes.annotate(
                neighbor.NM_MUN,
                (point.x, point.y),
                ha="center",
                va="center",
                fontsize=6.3,
                color=INK,
                family="DejaVu Serif",
                style="italic",
                zorder=121,
            )
            label.set_path_effects(
                [path_effects.withStroke(linewidth=2.0, foreground=PAPER)]
            )
    if visible_cities is not None:
        for city in visible_cities.sort_values("POP_RANK").itertuples():
            right_side = city.geometry.x > x_limits[0] + (x_limits[1] - x_limits[0]) * 0.78
            vertical_offset = 7 if city.NM_LOCALID == "Rio de Janeiro" else 2.5
            label = axes.annotate(
                city.NM_LOCALID,
                (city.geometry.x, city.geometry.y),
                xytext=(-4 if right_side else 3.5, vertical_offset),
                textcoords="offset points",
                ha="right" if right_side else "left",
                fontsize=6.2,
                color=INK,
                family="DejaVu Serif",
                style="italic",
                zorder=120,
            )
            label.set_path_effects([path_effects.withStroke(linewidth=2.2, foreground=PAPER)])
    axes.set_aspect("equal")
    add_globe_inset(
        figure,
        layers["world"],
        layers["states_wgs"],
        "",
        focus=focus,
        bounds=(0.835, 0.825, 0.14, 0.14),
        colors={
            "ocean": PAPER,
            "land": "#DADADA",
            "coast": "#707070",
            "grid": "#C8C8C8",
            "brazil": "#8A8A8A",
            "target": MUTED_INK,
            "ink": INK,
            "muted": MUTED_INK,
        },
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=300, facecolor=figure.get_facecolor())
    plt.close(figure)
    return {"synthetic": synthetic, "municipality_code": SAO_FELIX_CODE if "sao-felix" in slug else None}


def build_requested_series(output_root: Path | None = None, *, offline: bool = False) -> Path:
    """Build six bilingual bundles directly under ``outputs/<slug>/latest``."""
    output_root = output_root or ROOT / "outputs"
    layers, provenance = _load(offline)
    for slug in SERIES:
        with atomic_output(output_root, slug) as directory:
            files: dict[str, dict[str, object]] = {}
            statistics: dict[str, object] = {}
            for locale in LOCALES:
                png = directory / f"{slug}_{locale}.png"
                statistics = _render(slug, locale, layers, png)
                title, subtitle = COPY[slug][locale]
                description = f"{title}. {subtitle}. {RELIEF_COPY[locale]}"
                caption_text = description
                if "sao-felix" in slug:
                    caption_text += f"\n\n{OSM_ATTRIBUTION}."
                caption = directory / f"caption_{locale}.md"
                alt = directory / f"alt_{locale}.txt"
                caption.write_text(caption_text + "\n", encoding="utf-8")
                alt.write_text(description + "\n", encoding="utf-8")
                for path in (png, caption, alt):
                    files[path.name] = {"sha256": file_hash(path), "bytes": path.stat().st_size}
            manifest = {
                "schema_version": 1,
                "slug": slug,
                "maturity": "experimental" if statistics["synthetic"] else "validated",
                "locales": list(LOCALES),
                "layout": {"width_inches": 7.5, "height_inches": 7.5, "dpi": 300},
                "crs": DISPLAY_CRS,
                "statistics": statistics,
                "sequence": SERIES.index(slug) + 1,
                "sources": [
                    {
                        "source_id": item.source_id,
                        "edition": item.edition,
                        "sha256": item.sha256,
                        "size_bytes": item.size_bytes,
                    }
                    for item in provenance
                    if item.source_id
                    in (
                        {
                            "ibge_federation_units_2024",
                            "ibge_biomes_2025",
                            "ibge_localities_2022",
                            "natural_earth_admin_0_countries_5_1_2",
                            RELIEF_SOURCE_ID,
                        }
                        if slug in {"amazon-biome", "cerrado-biome", "amazon-cerrado-biomes"}
                        else {
                            "ibge_federation_units_2024",
                            "ibge_municipalities_2024",
                            "natural_earth_admin_0_countries_5_1_2",
                            "openstreetmap_norte_2026_08_09",
                            RELIEF_SOURCE_ID,
                            *(
                                {
                                    "mma_cnuc_2025_08",
                                    "funai_indigenous_lands_2026_08_11",
                                }
                                if slug == "sao-felix-do-xingu"
                                else set()
                            ),
                        }
                    )
                ],
                "privacy": {
                    "human_review_required": bool(statistics["synthetic"]),
                    "owner_or_supplier_identifiers": False,
                },
                "files": files,
                "review": {"status": "draft"},
            }
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            promote_output(directory, output_root / slug / "latest")
    return output_root
