"""Build ten bilingual visual studies of the Amazon and Cerrado map."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt

from ..components.globe import add_globe_inset
from ..data import Provenance, fetch_source
from ..export import atomic_output, file_hash, promote_output
from ..i18n import LOCALES, Locale
from .requested_series import (
    BIOME_NAMES,
    DISPLAY_CRS,
    MAJOR_CITIES,
    PAPER,
    RELIEF_COPY,
    RELIEF_SOURCE_ID,
    ROOT,
    _add_relief,
    _add_state_labels,
    _regional_world_land,
    _set_square_extent,
    municipality_geocode,
)

COLLECTION_SLUG = "amazon-cerrado-variations"


@dataclass(frozen=True)
class Variation:
    """Typed visual choices for one map study."""

    slug: str
    name_pt: str
    name_en: str
    amazon: str
    cerrado: str
    land: str
    ocean: str
    boundary: str
    state: str
    label: str
    relief_alpha: float
    fill_alpha: float = 0.90
    biome_linewidth: float = 0.65
    show_cities: bool = True


VARIATIONS = (
    Variation("version-01", "Editorial clássica", "Classic editorial", "#285943", "#D9B77E", "#D9D9D9", "#C5C5C5", "#505050", "#505050", "#505050", 0.18),
    Variation("version-02", "Floresta e solo", "Forest and soil", "#174A38", "#C98245", "#E4DED2", "#CBD5D2", "#3E433F", "#68645C", "#3E433F", 0.12),
    Variation("version-03", "Atlas escuro", "Dark atlas", "#2F725B", "#D5A34E", "#343A3C", "#20292D", "#E5E1D8", "#8A9292", "#ECE8DE", 0.24),
    Variation("version-04", "Campo claro", "Light field", "#4F8069", "#E5C891", "#EEECE6", "#DDE6E8", "#64645F", "#8E8D86", "#595A56", 0.08),
    Variation("version-05", "Alto contraste", "High contrast", "#0B503B", "#F0B44D", "#D1D4D2", "#AEBCC1", "#222624", "#363B39", "#242826", 0.16, 0.96, 0.95),
    Variation("version-06", "Terra suave", "Soft earth", "#56705F", "#C9A77C", "#D8D0C2", "#C4CDD0", "#5D574F", "#777168", "#565149", 0.15, 0.84),
    Variation("version-07", "Duotone", "Duotone", "#356859", "#B6A467", "#D6D8D3", "#C8CFCE", "#4D5753", "#707975", "#4D5753", 0.10, 0.92),
    Variation("version-08", "Contornos dominantes", "Boundary forward", "#6F927F", "#D8C39B", "#E1E0DB", "#CCD3D5", "#303735", "#4B5350", "#404643", 0.10, 0.72, 1.55),
    Variation("version-09", "Relevo dominante", "Relief forward", "#376C55", "#C89B5C", "#D3D3CF", "#BFC7C9", "#484E4B", "#666C69", "#464B49", 0.32, 0.76),
    Variation("version-10", "Minimalista", "Minimal", "#2D624F", "#D6B47A", "#E6E5E0", "#D4DADC", "#5E625F", "#8B8E8B", "#565A57", 0.04, 0.90, 0.55, False),
)


def _load_national() -> tuple[dict[str, object], list[Provenance]]:
    """Load only the verified sources shared by all ten national studies."""
    source_ids = {
        "states": "ibge_federation_units_2024",
        "biomes": "ibge_biomes_2025",
        "localities": "ibge_localities_2022",
        "world": "natural_earth_admin_0_countries_5_1_2",
        "relief": RELIEF_SOURCE_ID,
    }
    fetched = {key: fetch_source(value) for key, value in source_ids.items()}
    states_wgs = gpd.read_file(fetched["states"][0])
    city_codes = [municipality_geocode(name, state) for name, state in MAJOR_CITIES]
    candidates = gpd.read_file(
        fetched["localities"][0],
        columns=["CD_MUN", "CT_LOCALID", "SCT_LOCALI", "NM_LOCALID", "geometry"],
    )
    candidates = candidates.loc[
        candidates.CD_MUN.isin(city_codes) & (candidates.CT_LOCALID == "Cidade")
    ]
    selected = []
    for code in city_codes:
        options = candidates.loc[candidates.CD_MUN == code]
        capital = options.loc[options.SCT_LOCALI.str.startswith("Capital", na=False)]
        seat = capital if not capital.empty else options.loc[options.SCT_LOCALI == "Sede Municipal"]
        if len(seat) != 1:
            raise ValueError(f"expected one official IBGE capital or municipal seat for {code}")
        selected.append(seat.iloc[0])
    cities = gpd.GeoDataFrame(selected, crs=candidates.crs).to_crs(DISPLAY_CRS)
    cities["POP_RANK"] = range(len(cities))
    return (
        {
            "states": states_wgs.to_crs(DISPLAY_CRS),
            "states_wgs": gpd.GeoDataFrame(
                geometry=[states_wgs.geometry.union_all().simplify(0.08, preserve_topology=True)],
                crs=states_wgs.crs,
            ),
            "biomes": gpd.read_file(fetched["biomes"][0]).to_crs(DISPLAY_CRS),
            "cities": cities,
            "world": gpd.read_file(fetched["world"][0]).assign(
                geometry=lambda frame: frame.geometry.simplify(0.08, preserve_topology=True)
            ),
            "world_display": _regional_world_land(fetched["world"][0]),
            "relief": fetched["relief"][0],
        },
        [item[1] for item in fetched.values()],
    )


def _legend(figure: plt.Figure, locale: Locale, style: Variation) -> None:
    labels = ["Amazônia" if locale == "pt-BR" else "Amazon", "Cerrado"]
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor=style.boundary, linewidth=0.5)
        for color in (style.amazon, style.cerrado)
    ]
    legend = figure.legend(
        handles,
        labels,
        loc="lower left",
        bbox_to_anchor=(0.022, 0.025),
        frameon=True,
        fancybox=False,
        framealpha=0.76,
        facecolor=PAPER,
        edgecolor="none",
        fontsize=16,
        labelcolor=style.label,
    )
    legend.get_frame().set_linewidth(0)


def _render(style: Variation, locale: Locale, layers: dict[str, object], target: Path) -> None:
    figure = plt.figure(figsize=(7.5, 7.5), facecolor=style.ocean)
    axes = figure.add_axes((0, 0, 1, 1), facecolor=style.ocean)
    axes.set_axis_off()
    biomes = layers["biomes"]
    amazon = biomes.loc[biomes.NM_BIOMA == BIOME_NAMES["amazon"]]
    cerrado = biomes.loc[biomes.NM_BIOMA == BIOME_NAMES["cerrado"]]
    if len(amazon) != 1 or len(cerrado) != 1:
        raise ValueError("expected exactly one official Amazon and Cerrado biome feature")
    focus = gpd.GeoDataFrame(
        geometry=[amazon.geometry.union_all().union(cerrado.geometry.union_all())], crs=amazon.crs
    )
    layers["world_display"].plot(ax=axes, color=style.land, edgecolor="none", zorder=1)
    layers["states"].plot(ax=axes, color=style.land, edgecolor=PAPER, linewidth=0.25, zorder=3)
    focus.boundary.plot(ax=axes, color=PAPER, linewidth=style.biome_linewidth + 1.25, zorder=8)
    amazon.plot(ax=axes, color=style.amazon, alpha=style.fill_alpha, edgecolor=style.boundary, linewidth=style.biome_linewidth, zorder=10)
    cerrado.plot(ax=axes, color=style.cerrado, alpha=style.fill_alpha, edgecolor=style.boundary, linewidth=style.biome_linewidth, zorder=10)
    _set_square_extent(axes, list(layers["states"].total_bounds), padding_ratio=0.03)
    _add_relief(axes, layers["relief"], alpha=style.relief_alpha)
    x_limits, y_limits = axes.get_xlim(), axes.get_ylim()
    visible_cities = layers["cities"].cx[x_limits[0] : x_limits[1], y_limits[0] : y_limits[1]]
    accepted = []
    points = []
    minimum_distance = (x_limits[1] - x_limits[0]) * 0.055
    for city in visible_cities.sort_values("POP_RANK").itertuples():
        if any(city.geometry.distance(point) < minimum_distance for point in points):
            continue
        accepted.append(city.Index)
        points.append(city.geometry)
    visible_cities = visible_cities.loc[accepted]
    if style.show_cities:
        visible_cities.plot(ax=axes, color=style.label, edgecolor=PAPER, linewidth=0.5, markersize=17, zorder=80)
    layers["states"].boundary.plot(ax=axes, color=style.state, linewidth=0.48, zorder=100)
    axes.set_xlim(x_limits)
    axes.set_ylim(y_limits)
    _add_state_labels(axes, layers["states"], local=False)
    if style.show_cities:
        for city in visible_cities.sort_values("POP_RANK").itertuples():
            right = city.geometry.x > x_limits[0] + (x_limits[1] - x_limits[0]) * 0.78
            label = axes.annotate(
                city.NM_LOCALID,
                (city.geometry.x, city.geometry.y),
                xytext=(-4 if right else 3.5, 2.5),
                textcoords="offset points",
                ha="right" if right else "left",
                fontsize=6.2,
                color=style.label,
                family="DejaVu Serif",
                style="italic",
                zorder=120,
            )
            label.set_path_effects([path_effects.withStroke(linewidth=2.2, foreground=PAPER)])
    _legend(figure, locale, style)
    axes.set_aspect("equal")
    add_globe_inset(
        figure,
        layers["world"],
        layers["states_wgs"],
        "",
        focus=focus,
        bounds=(0.835, 0.825, 0.14, 0.14),
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(target, dpi=300, facecolor=figure.get_facecolor())
    plt.close(figure)


def build_biome_variations(output_root: Path | None = None) -> Path:
    """Build ten bilingual visual studies in one flat collection folder."""
    base_output = output_root or ROOT / "outputs"
    destination = base_output / COLLECTION_SLUG
    layers, provenance = _load_national()
    with atomic_output(base_output, COLLECTION_SLUG) as directory:
        for sequence, style in enumerate(VARIATIONS, start=1):
            files: dict[str, dict[str, object]] = {}
            for locale in LOCALES:
                png = directory / f"amazon-cerrado-{style.slug}_{locale}.png"
                _render(style, locale, layers, png)
                style_name = style.name_pt if locale == "pt-BR" else style.name_en
                title = "Amazônia e Cerrado" if locale == "pt-BR" else "Amazon and Cerrado"
                subtitle = "Limites oficiais do IBGE · 2025" if locale == "pt-BR" else "Official IBGE boundaries · 2025"
                description = f"{title}. {style_name}. {subtitle}. {RELIEF_COPY[locale]}"
                caption = directory / f"caption-{style.slug}_{locale}.md"
                alt = directory / f"alt-{style.slug}_{locale}.txt"
                caption.write_text(description + "\n", encoding="utf-8")
                alt.write_text(description + "\n", encoding="utf-8")
                for path in (png, caption, alt):
                    files[path.name] = {"sha256": file_hash(path), "bytes": path.stat().st_size}
            manifest = {
                "schema_version": 1,
                "collection": COLLECTION_SLUG,
                "slug": style.slug,
                "sequence": sequence,
                "maturity": "design-study",
                "locales": list(LOCALES),
                "layout": {"width_inches": 7.5, "height_inches": 7.5, "dpi": 300},
                "crs": DISPLAY_CRS,
                "style": asdict(style),
                "sources": [
                    {"source_id": item.source_id, "edition": item.edition, "sha256": item.sha256, "size_bytes": item.size_bytes}
                    for item in provenance
                ],
                "files": files,
                "review": {"status": "draft"},
            }
            (directory / f"manifest-{style.slug}.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        promote_output(directory, destination)
    return destination
