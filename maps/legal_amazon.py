"""Generate bilingual editorial maps of the Legal Amazon.

Data sources
------------
IBGE, Legal Amazon boundary, edition 2024.
IBGE, Digital Municipal Mesh (Federation Units), edition 2024.
Accessed programmatically from the official IBGE GeoFTP service.
"""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Rectangle
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ibge"
OUTPUT = ROOT / "outputs"
CRS_MAP = "EPSG:5880"  # SIRGAS 2000 / Brazil Polyconic

SOURCES = {
    "legal_amazon": {
        "url": (
            "https://geoftp.ibge.gov.br/organizacao_do_territorio/"
            "estrutura_territorial/amazonia_legal/2024/"
            "Limites_Amazonia_Legal_2024_shp.zip"
        ),
        "folder": RAW / "amazonia_legal_2024",
        "shp": "Limites_Amazonia_Legal_2024.shp",
    },
    "states": {
        "url": (
            "https://geoftp.ibge.gov.br/organizacao_do_territorio/"
            "malhas_territoriais/malhas_municipais/municipio_2024/"
            "Brasil/BR_UF_2024.zip"
        ),
        "folder": RAW / "malhas_2024",
        "shp": "BR_UF_2024.shp",
    },
}

TEXT = {
    "pt-BR": {
        "title": "A Amazônia Legal ocupa quase 60% do Brasil",
        "subtitle": (
            "O recorte reúne nove estados e 773 municípios; no Maranhão, "
            "apenas a porção a oeste do meridiano 44° integra a região."
        ),
        "label": "Amazônia Legal",
        "context": "Demais áreas do Brasil",
        "area": "5,01 milhões\nde km²",
        "share": "58,9% do território nacional",
        "scale": "500 km",
        "inset": "Brasil no mundo",
        "source": (
            "Fonte: IBGE, Limites da Amazônia Legal e Malha Municipal Digital, "
            "edições 2024. CRS: SIRGAS 2000 / Brazil Polyconic."
        ),
    },
    "en-US": {
        "title": "The Legal Amazon covers nearly 60% of Brazil",
        "subtitle": (
            "The region spans nine states and 773 municipalities; in Maranhão, "
            "only the area west of the 44th meridian is included."
        ),
        "label": "Legal Amazon",
        "context": "Rest of Brazil",
        "area": "5.01 million\nkm²",
        "share": "58.9% of Brazil's territory",
        "scale": "500 km",
        "inset": "Brazil in the world",
        "source": (
            "Source: IBGE, Legal Amazon Boundaries and Digital Municipal Mesh, "
            "2024 editions. CRS: SIRGAS 2000 / Brazil Polyconic."
        ),
    },
}

COLORS = {
    "paper": "#F7F4EE",
    "land": "#DDDCD6",
    "state_line": "#FFFFFF",
    "amazon": "#1E786A",
    "amazon_edge": "#11574D",
    "ink": "#222222",
    "muted": "#6E6D68",
    "ocean": "#DDE8E6",
    "globe_line": "#A9BEBA",
    "locator": "#D67C42",
}


def ensure_source(item: dict[str, object]) -> Path:
    folder = Path(item["folder"])
    shp = folder / str(item["shp"])
    if shp.exists():
        return shp

    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / Path(str(item["url"])).name
    if not archive.exists():
        print(f"Downloading {item['url']}")
        urlretrieve(str(item["url"]), archive)
    with ZipFile(archive) as zipped:
        zipped.extractall(folder)
    return shp


def add_scale_bar(ax: plt.Axes, label: str) -> None:
    """Draw a 500 km scale bar in projected map units (metres)."""
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    length = 500_000
    x0 = xmin + (xmax - xmin) * 0.065
    y0 = ymin + (ymax - ymin) * 0.08
    height = (ymax - ymin) * 0.009
    ax.add_patch(Rectangle((x0, y0), length / 2, height, color=COLORS["ink"], zorder=5))
    ax.add_patch(
        Rectangle(
            (x0 + length / 2, y0), length / 2, height,
            facecolor=COLORS["paper"], edgecolor=COLORS["ink"], linewidth=0.8, zorder=5,
        )
    )
    ax.text(
        x0 + length / 2, y0 + height * 2.1, label,
        ha="center", va="bottom", fontsize=9, color=COLORS["ink"],
    )


def add_globe_inset(fig: plt.Figure, states_wgs84: gpd.GeoDataFrame, label: str) -> None:
    """Add an orthographic locator globe centered on Brazil."""
    globe = fig.add_axes((0.765, 0.205, 0.17, 0.17), facecolor="none")
    radius = 6_371_000
    boundary = Circle(
        (0, 0), radius, facecolor=COLORS["ocean"],
        edgecolor=COLORS["ink"], linewidth=0.8, zorder=0,
    )
    globe.add_patch(boundary)

    transformer = Transformer.from_crs(
        "EPSG:4674", "+proj=ortho +lat_0=-15 +lon_0=-55 +ellps=GRS80 +units=m",
        always_xy=True,
    )

    def plot_graticule(lons: list[float], lats: list[float]) -> None:
        xs, ys = transformer.transform(lons, lats)
        segment_x: list[float] = []
        segment_y: list[float] = []
        for x, y in zip(xs, ys, strict=True):
            if abs(x) <= radius and abs(y) <= radius:
                segment_x.append(x)
                segment_y.append(y)
            elif segment_x:
                globe.plot(segment_x, segment_y, color=COLORS["globe_line"], linewidth=0.35, zorder=1)
                segment_x, segment_y = [], []
        if segment_x:
            globe.plot(segment_x, segment_y, color=COLORS["globe_line"], linewidth=0.35, zorder=1)

    samples = list(range(-180, 181, 2))
    for latitude in (-60, -30, 0, 30, 60):
        plot_graticule(samples, [latitude] * len(samples))
    lat_samples = list(range(-89, 90, 2))
    for longitude in range(-180, 180, 30):
        plot_graticule([longitude] * len(lat_samples), lat_samples)

    brazil = states_wgs84.dissolve().to_crs(
        "+proj=ortho +lat_0=-15 +lon_0=-55 +ellps=GRS80 +units=m"
    )
    brazil.plot(
        ax=globe, facecolor=COLORS["locator"], edgecolor=COLORS["ink"],
        linewidth=0.45, zorder=3,
    )
    globe.set_xlim(-radius * 1.04, radius * 1.04)
    globe.set_ylim(-radius * 1.04, radius * 1.04)
    globe.set_aspect("equal")
    globe.set_axis_off()
    globe.text(
        0.5, -0.08, label, transform=globe.transAxes, ha="center", va="top",
        fontsize=6.8, color=COLORS["muted"],
    )
def render(
    language: str,
    states: gpd.GeoDataFrame,
    amazon: gpd.GeoDataFrame,
    states_wgs84: gpd.GeoDataFrame,
) -> None:
    copy = TEXT[language]
    fig = plt.figure(figsize=(7.5, 7.5), facecolor=COLORS["paper"])
    ax = fig.add_axes((0.055, 0.16, 0.65, 0.60), facecolor=COLORS["paper"])

    states.plot(
        ax=ax, facecolor=COLORS["land"], edgecolor=COLORS["state_line"],
        linewidth=0.75, zorder=1,
    )
    amazon.plot(
        ax=ax, facecolor=COLORS["amazon"], edgecolor=COLORS["amazon_edge"],
        linewidth=1.25, zorder=2,
    )
    states.boundary.plot(ax=ax, color="#B9B8B2", linewidth=0.35, zorder=3)

    minx, miny, maxx, maxy = states.total_bounds
    pad_x = (maxx - minx) * 0.025
    pad_y = (maxy - miny) * 0.03
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_axis_off()
    ax.set_aspect("equal")
    add_scale_bar(ax, copy["scale"])
    add_globe_inset(fig, states_wgs84, copy["inset"])

    fig.text(
        0.055, 0.945, copy["title"], ha="left", va="top",
        fontsize=19, weight="bold", color=COLORS["ink"],
    )
    fig.text(
        0.055, 0.885, copy["subtitle"], ha="left", va="top",
        fontsize=9.2, color=COLORS["muted"], linespacing=1.35, wrap=True,
    )

    fig.text(0.715, 0.64, copy["area"], fontsize=16, weight="bold", color=COLORS["amazon"], linespacing=1.05)
    fig.text(0.715, 0.555, copy["share"], fontsize=9, color=COLORS["ink"], wrap=True)
    fig.add_artist(Line2D([0.715, 0.95], [0.515, 0.515], transform=fig.transFigure,
                          color="#C9C6BE", linewidth=0.8))

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=COLORS["amazon"], edgecolor="none"),
        Rectangle((0, 0), 1, 1, facecolor=COLORS["land"], edgecolor="none"),
    ]
    fig.legend(
        legend_handles, [copy["label"], copy["context"]], loc="upper left",
        bbox_to_anchor=(0.705, 0.49), frameon=False, fontsize=8.5,
        handlelength=1.2, handleheight=1.2, labelspacing=0.9,
    )

    fig.text(
        0.055, 0.035, copy["source"], ha="left", va="bottom",
        fontsize=6.5, color=COLORS["muted"], wrap=True,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stem = OUTPUT / f"legal_amazon_{language}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor=fig.get_facecolor())
    fig.savefig(stem.with_suffix(".pdf"), facecolor=fig.get_facecolor())
    fig.savefig(stem.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    states_wgs84 = gpd.read_file(ensure_source(SOURCES["states"]))
    states = states_wgs84.to_crs(CRS_MAP)
    amazon = gpd.read_file(ensure_source(SOURCES["legal_amazon"])).to_crs(CRS_MAP)
    for language in TEXT:
        render(language, states, amazon, states_wgs84)
        print(f"Generated {language}")


if __name__ == "__main__":
    main()
