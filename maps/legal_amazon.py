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
from matplotlib.patches import Rectangle


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
        "area": "5,01 milhões de km²",
        "share": "58,9% do território nacional",
        "scale": "500 km",
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
        "area": "5.01 million km²",
        "share": "58.9% of Brazil's territory",
        "scale": "500 km",
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


def render(language: str, states: gpd.GeoDataFrame, amazon: gpd.GeoDataFrame) -> None:
    copy = TEXT[language]
    fig = plt.figure(figsize=(13.33, 7.5), facecolor=COLORS["paper"])
    ax = fig.add_axes((0.045, 0.12, 0.62, 0.70), facecolor=COLORS["paper"])

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

    fig.text(
        0.055, 0.925, copy["title"], ha="left", va="top",
        fontsize=24, weight="bold", color=COLORS["ink"],
    )
    fig.text(
        0.055, 0.855, copy["subtitle"], ha="left", va="top",
        fontsize=11.5, color=COLORS["muted"], linespacing=1.35,
    )

    fig.text(0.705, 0.66, copy["area"], fontsize=21, weight="bold", color=COLORS["amazon"])
    fig.text(0.705, 0.605, copy["share"], fontsize=12, color=COLORS["ink"])
    fig.add_artist(Line2D([0.705, 0.92], [0.57, 0.57], transform=fig.transFigure,
                          color="#C9C6BE", linewidth=0.8))

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=COLORS["amazon"], edgecolor="none"),
        Rectangle((0, 0), 1, 1, facecolor=COLORS["land"], edgecolor="none"),
    ]
    fig.legend(
        legend_handles, [copy["label"], copy["context"]], loc="upper left",
        bbox_to_anchor=(0.698, 0.53), frameon=False, fontsize=10,
        handlelength=1.2, handleheight=1.2, labelspacing=0.9,
    )

    fig.text(
        0.055, 0.035, copy["source"], ha="left", va="bottom",
        fontsize=8, color=COLORS["muted"],
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    stem = OUTPUT / f"legal_amazon_{language}"
    fig.savefig(stem.with_suffix(".png"), dpi=300, facecolor=fig.get_facecolor())
    fig.savefig(stem.with_suffix(".pdf"), facecolor=fig.get_facecolor())
    fig.savefig(stem.with_suffix(".svg"), facecolor=fig.get_facecolor())
    plt.close(fig)


def main() -> None:
    states = gpd.read_file(ensure_source(SOURCES["states"])).to_crs(CRS_MAP)
    amazon = gpd.read_file(ensure_source(SOURCES["legal_amazon"])).to_crs(CRS_MAP)
    for language in TEXT:
        render(language, states, amazon)
        print(f"Generated {language}")


if __name__ == "__main__":
    main()
