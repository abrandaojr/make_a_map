"""Governed vertical slice: official 2024 Legal Amazon boundary."""

from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt

from ..components.globe import add_globe_inset
from ..components.legend import LegendItem, draw_legend
from ..components.scale import draw_scale_bar
from ..components.source import source_line
from ..contracts import LayoutSpec, MapSpec, Quantity, SourceSpec, Statistic
from ..data import Provenance, fetch_source, load_catalog
from ..export import atomic_output, finalize_build
from ..i18n import LOCALES, Locale, TranslationCatalog, format_number
from ..layout import get_layout
from ..theme import DEFAULT_THEME, Theme

ROOT = Path(__file__).resolve().parents[3]
DISPLAY_CRS = "EPSG:5880"
CRS_LABEL = "SIRGAS 2000 / Brazil Polyconic"
DISPLAY_SIMPLIFICATION_M = 2_500


CATALOG = TranslationCatalog(
    {
        "pt-BR": {
            "title": {
                "scientific": "Limites da Amazônia Legal, Brasil, 2024",
                "editorial": "A Amazônia Legal ocupa {share} do território brasileiro",
            },
            "subtitle": (
                "Recorte territorial oficial de 2024; no Maranhão, somente a área "
                "a oeste do meridiano 44° está incluída."
            ),
            "stat": {
                "label": "Área oficial",
                "unit": "milhões de km²",
                "note": "{share} do Brasil",
            },
            "legend": {"focus": "Amazônia Legal", "context": "Demais áreas do Brasil"},
            "scale": "500 km",
            "globe": "Brasil no mundo",
            "caption": (
                "Limite oficial da Amazônia Legal em 2024, destacado em verde. "
                "O restante do território brasileiro aparece em cinza."
            ),
            "alt": (
                "Mapa do Brasil destacando a Amazônia Legal, que ocupa {share} do "
                "território nacional e possui área oficial de {area}."
            ),
        },
        "en-US": {
            "title": {
                "scientific": "Legal Amazon boundaries, Brazil, 2024",
                "editorial": "The Legal Amazon covers {share} of Brazil's territory",
            },
            "subtitle": (
                "Official 2024 territorial boundary; in Maranhão, only the area west "
                "of the 44th meridian is included."
            ),
            "stat": {"label": "Official area", "unit": "million km²", "note": "{share} of Brazil"},
            "legend": {"focus": "Legal Amazon", "context": "Rest of Brazil"},
            "scale": "500 km",
            "globe": "Brazil in the world",
            "caption": (
                "Official 2024 Legal Amazon boundary, highlighted in green. "
                "The rest of Brazil is shown in gray."
            ),
            "alt": (
                "Map of Brazil highlighting the Legal Amazon, which covers {share} "
                "of the country and has an official area of {area}."
            ),
        },
    }
)


def _source_specs() -> tuple[SourceSpec, ...]:
    catalog = load_catalog()
    return tuple(
        SourceSpec(
            source_id=item.id,
            publisher=item.publisher,
            product=item.title,
            edition=item.edition,
            url=item.url,
            accessed=date(2026, 8, 10),
            original_crs=item.crs_original or "unknown",
            sha256=item.sha256,
        )
        for item in (
            catalog["ibge_legal_amazon_2024"],
            catalog["ibge_federation_units_2024"],
            catalog["natural_earth_admin_0_countries_5_1_2"],
        )
    )


def create_spec(mode: str = "editorial") -> MapSpec:
    return MapSpec(
        slug="legal-amazon",
        mode=mode,  # type: ignore[arg-type]
        crs=DISPLAY_CRS,
        catalog=CATALOG,
        sources=_source_specs(),
        statistics=(Statistic("stat.label", Quantity(0, "stat.unit", decimals=2), "stat.note"),),
        layout=LayoutSpec(),
    )


def _read_and_validate(path: Path, expected_crs: str, source_id: str) -> gpd.GeoDataFrame:
    frame = gpd.read_file(path)
    if frame.empty or frame.crs is None:
        raise ValueError(f"{source_id} is empty or has no CRS")
    if frame.crs.to_epsg() != gpd.GeoSeries([], crs=expected_crs).crs.to_epsg():
        raise ValueError(f"{source_id} CRS mismatch: {frame.crs}, expected {expected_crs}")
    if frame.geometry.is_empty.any() or frame.geometry.isna().any():
        raise ValueError(f"{source_id} contains empty geometry")
    if not frame.geometry.is_valid.all():
        raise ValueError(f"{source_id} contains invalid geometry; repair must be explicit")
    return frame


def prepare(
    offline: bool = False,
) -> tuple[dict[str, gpd.GeoDataFrame], list[Provenance], dict[str, float]]:
    ids = (
        "ibge_legal_amazon_2024",
        "ibge_federation_units_2024",
        "natural_earth_admin_0_countries_5_1_2",
    )
    fetched = [fetch_source(source_id, offline=offline) for source_id in ids]
    provenances = [item[1] for item in fetched]
    legal = _read_and_validate(fetched[0][0], "EPSG:4674", ids[0])
    states_wgs84 = _read_and_validate(fetched[1][0], "EPSG:4674", ids[1])
    world = _read_and_validate(fetched[2][0], "EPSG:4326", ids[2])

    official_area = float(legal["AREA_KM2"].sum())
    brazil_area = float(states_wgs84["AREA_KM2"].sum())
    statistics = {
        "area_million_km2": official_area / 1_000_000,
        "share": official_area / brazil_area,
    }

    states = states_wgs84.to_crs(DISPLAY_CRS).copy()
    legal_display = legal.to_crs(DISPLAY_CRS).copy()
    # Generalization applies only to display copies, never analytical values.
    states.geometry = states.geometry.simplify(DISPLAY_SIMPLIFICATION_M, preserve_topology=True)
    legal_display.geometry = legal_display.geometry.simplify(
        DISPLAY_SIMPLIFICATION_M, preserve_topology=True
    )
    return (
        {
            "states": states,
            "states_wgs84": states_wgs84,
            "legal": legal_display,
            "world": world,
        },
        provenances,
        statistics,
    )


def _wrap(value: str, width: int, max_lines: int) -> str:
    lines = textwrap.wrap(value, width=width, break_long_words=False, break_on_hyphens=False)
    if len(lines) > max_lines:
        raise ValueError(f"text exceeds the {max_lines}-line layout budget: {value!r}")
    return "\n".join(lines)


def _assert_text_inside(figure: plt.Figure) -> None:
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    figure_box = figure.bbox
    for artist in figure.texts:
        box = artist.get_window_extent(renderer=renderer)
        if not figure_box.contains(box.x0, box.y0) or not figure_box.contains(box.x1, box.y1):
            raise ValueError(f"text leaves the figure: {artist.get_text()!r}")


def render_locale(
    locale: Locale,
    spec: MapSpec,
    layers: dict[str, gpd.GeoDataFrame],
    provenance: list[Provenance],
    statistics: dict[str, float],
    output_dir: Path,
    theme: Theme = DEFAULT_THEME,
) -> dict[str, str]:
    slots = get_layout("map-plus-metric")
    share = format_number(statistics["share"] * 100, locale, 1) + "%"
    area = Quantity(statistics["area_million_km2"], "stat.unit", 2).format(locale, CATALOG)
    title = CATALOG.get(locale, f"title.{spec.mode}").format(share=share)
    subtitle = CATALOG.get(locale, "subtitle")

    mpl.rcParams.update(
        {
            "font.family": theme.typography.family,
            "svg.hashsalt": "make-a-map-v1",
            "axes.unicode_minus": False,
        }
    )
    fig = plt.figure(
        figsize=(spec.layout.width_inches, spec.layout.height_inches),
        facecolor=theme.colors.paper,
    )
    ax = fig.add_axes(
        (slots.map_body.left, slots.map_body.bottom, slots.map_body.width, slots.map_body.height)
    )
    layers["states"].plot(
        ax=ax,
        facecolor=theme.colors.context_fill,
        edgecolor=theme.colors.boundary_light,
        linewidth=theme.strokes.context,
        zorder=1,
    )
    layers["legal"].plot(
        ax=ax,
        facecolor=theme.colors.data_primary,
        edgecolor=theme.colors.data_primary_edge,
        linewidth=theme.strokes.emphasis,
        zorder=2,
    )
    layers["states"].boundary.plot(
        ax=ax, color=theme.colors.context_line, linewidth=theme.strokes.hairline, zorder=3
    )
    minx, miny, maxx, maxy = layers["states"].total_bounds
    ax.set_xlim(minx - (maxx - minx) * 0.025, maxx + (maxx - minx) * 0.025)
    ax.set_ylim(miny - (maxy - miny) * 0.03, maxy + (maxy - miny) * 0.03)
    ax.set_aspect("equal")
    ax.set_axis_off()
    draw_scale_bar(ax, spec.crs, CATALOG.get(locale, "scale"), theme)

    add_globe_inset(
        fig,
        layers["world"],
        layers["states_wgs84"],
        CATALOG.get(locale, "globe"),
        bounds=(slots.globe.left, slots.globe.bottom, slots.globe.width, slots.globe.height),
        colors={
            "ocean": theme.colors.water,
            "land": theme.colors.context_fill,
            "coast": theme.colors.context_line,
            "grid": theme.colors.graticule,
            "brazil": theme.colors.data_accent,
            "ink": theme.colors.ink,
            "muted": theme.colors.muted_ink,
        },
    )

    fig.text(
        slots.header.left,
        slots.header.top,
        _wrap(title, 44, 2),
        ha="left",
        va="top",
        fontsize=theme.typography.title_size,
        weight="bold",
        color=theme.colors.ink,
        linespacing=1.05,
    )
    fig.text(
        slots.header.left,
        slots.header.top - 0.085,
        _wrap(subtitle, 76, 2),
        ha="left",
        va="top",
        fontsize=theme.typography.subtitle_size,
        color=theme.colors.muted_ink,
        linespacing=1.25,
    )
    fig.text(
        slots.rail.left,
        slots.rail.top - 0.03,
        _wrap(area, 14, 2),
        ha="left",
        va="top",
        fontsize=theme.typography.title_size - 2,
        weight="bold",
        color=theme.colors.data_primary,
    )
    fig.text(
        slots.rail.left,
        slots.rail.top - 0.13,
        CATALOG.get(locale, "stat.note").format(share=share),
        ha="left",
        va="top",
        fontsize=theme.typography.body_size,
        color=theme.colors.ink,
    )
    draw_legend(
        fig,
        (
            LegendItem(CATALOG.get(locale, "legend.focus"), theme.colors.data_primary),
            LegendItem(CATALOG.get(locale, "legend.context"), theme.colors.context_fill),
        ),
        (slots.rail.left - 0.01, slots.rail.top - 0.19),
        theme,
    )
    fig.text(
        slots.source.left,
        slots.source.bottom,
        _wrap(source_line(locale, provenance[:2], CRS_LABEL), 118, 2),
        ha="left",
        va="bottom",
        fontsize=theme.typography.note_size,
        color=theme.colors.muted_ink,
    )
    _assert_text_inside(fig)

    output_dir.mkdir(parents=True, exist_ok=True)
    for extension in spec.layout.formats:
        path = output_dir / spec.output_name(locale, extension)
        kwargs: dict[str, object] = {"facecolor": fig.get_facecolor()}
        if extension in {"png", "tiff"}:
            kwargs["dpi"] = spec.layout.dpi
        if extension == "pdf":
            kwargs["metadata"] = {"CreationDate": None, "ModDate": None}
        fig.savefig(path, **kwargs)
    plt.close(fig)
    caption = CATALOG.get(locale, "caption")
    alt = CATALOG.get(locale, "alt").format(share=share, area=area)
    (output_dir / f"caption_{locale}.md").write_text(caption + "\n", encoding="utf-8")
    (output_dir / f"alt_{locale}.txt").write_text(alt + "\n", encoding="utf-8")
    return {"caption": caption, "alt": alt}


def build(output_root: Path | None = None, offline: bool = False, mode: str = "editorial") -> Path:
    spec = create_spec(mode)
    output_root = output_root or ROOT / "outputs"
    layers, provenance, statistics = prepare(offline=offline)
    destination = output_root / spec.slug / "latest"
    with atomic_output(output_root, spec.slug) as staging:
        accessibility = {
            locale: render_locale(locale, spec, layers, provenance, statistics, staging)
            for locale in LOCALES
        }
        # Sidecars are deliberately included in the manifest but not required by LayoutSpec.
        result = finalize_build(
            staging,
            destination,
            spec,
            {
                "maturity": "experimental",
                "recipe": "legal-amazon-municipalities",
                "analysis": {
                    "display_crs": DISPLAY_CRS,
                    "source_geometry_simplification_m": DISPLAY_SIMPLIFICATION_M,
                    "official_area_km2": statistics["area_million_km2"] * 1_000_000,
                    "share_of_brazil": statistics["share"],
                },
                "sources": [item.as_dict() for item in provenance],
                "accessibility": accessibility,
                "claims": {
                    "headline_share": {
                        "value": statistics["share"],
                        "derivation": "Legal Amazon AREA_KM2 / sum of federation-unit AREA_KM2",
                    }
                },
            },
        )
    return result
