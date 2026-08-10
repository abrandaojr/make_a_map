"""Orthographic world locator with an official IBGE Brazil highlight."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from pyproj import CRS, Geod, Transformer
from shapely.ops import transform as geometry_transform

ORTHOGRAPHIC_CRS = CRS.from_proj4(
    "+proj=ortho +lat_0=-15 +lon_0=-55 +ellps=GRS80 +units=m +no_defs"
)
GLOBE_RADIUS = 6_371_000
DEFAULT_COLORS = {
    "ocean": "#DDE8E6",
    "land": "#C9CEC9",
    "coast": "#89918C",
    "grid": "#A9BEBA",
    "brazil": "#D67C42",
    "ink": "#222222",
    "muted": "#6E6D68",
}


def _visible_hemisphere(world: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Project stable foreground countries and omit geometries crossing the horizon."""
    geographic = world.to_crs("EPSG:4326")
    geod = Geod(ellps="GRS80")
    projector = Transformer.from_crs("EPSG:4326", ORTHOGRAPHIC_CRS, always_xy=True)
    geometries = []
    for geometry in geographic.geometry:
        point = geometry.representative_point()
        _, _, distance = geod.inv(-55.0, -15.0, point.x, point.y)
        if distance > 8_500_000:
            continue
        projected = geometry_transform(projector.transform, geometry)
        bounds = np.asarray(projected.bounds)
        if np.isfinite(bounds).all() and np.abs(bounds).max() <= GLOBE_RADIUS * 1.05:
            geometries.append(projected)
    return gpd.GeoDataFrame(geometry=geometries, crs=ORTHOGRAPHIC_CRS)


def _graticule(ax: plt.Axes, transformer: Transformer, color: str) -> None:
    def line(longitudes: np.ndarray, latitudes: np.ndarray) -> None:
        x, y = transformer.transform(longitudes, latitudes)
        valid = np.isfinite(x) & np.isfinite(y) & (x * x + y * y <= GLOBE_RADIUS**2 * 1.002)
        indices = np.flatnonzero(valid)
        if not indices.size:
            return
        for segment in np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1):
            if segment.size >= 2:
                ax.plot(x[segment], y[segment], color=color, linewidth=0.3, zorder=1)

    longitude_samples = np.linspace(-180, 180, 361)
    for latitude in (-60, -30, 0, 30, 60):
        line(longitude_samples, np.full_like(longitude_samples, latitude))
    latitude_samples = np.linspace(-89.9, 89.9, 181)
    for longitude in range(-180, 180, 30):
        line(np.full_like(latitude_samples, longitude), latitude_samples)


def draw_globe(
    ax: plt.Axes,
    world: gpd.GeoDataFrame,
    brazil_ibge: gpd.GeoDataFrame,
    *,
    label: str | None = None,
    colors: Mapping[str, str] | None = None,
) -> None:
    """Draw a locator globe; ``brazil_ibge`` must be official IBGE geometry."""
    palette = {**DEFAULT_COLORS, **(colors or {})}
    boundary = Circle(
        (0, 0),
        GLOBE_RADIUS,
        facecolor=palette["ocean"],
        edgecolor=palette["ink"],
        linewidth=0.75,
        zorder=0,
    )
    ax.add_patch(boundary)
    transformer = Transformer.from_crs("EPSG:4326", ORTHOGRAPHIC_CRS, always_xy=True)
    _graticule(ax, transformer, palette["grid"])

    world_projected = _visible_hemisphere(world)
    world_projected.plot(
        ax=ax,
        facecolor=palette["land"],
        edgecolor=palette["coast"],
        linewidth=0.2,
        zorder=2,
    )
    brazil_ibge.to_crs(ORTHOGRAPHIC_CRS).dissolve().plot(
        ax=ax,
        facecolor=palette["brazil"],
        edgecolor=palette["ink"],
        linewidth=0.4,
        zorder=3,
    )
    for artist in ax.collections:
        artist.set_clip_path(boundary)
    ax.set_xlim(-GLOBE_RADIUS * 1.04, GLOBE_RADIUS * 1.04)
    ax.set_ylim(-GLOBE_RADIUS * 1.04, GLOBE_RADIUS * 1.04)
    ax.set_aspect("equal")
    ax.set_axis_off()
    if label:
        ax.text(
            0.5,
            -0.075,
            label,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=6.8,
            color=palette["muted"],
        )


def add_globe_inset(
    figure: plt.Figure,
    world: gpd.GeoDataFrame,
    brazil_ibge: gpd.GeoDataFrame,
    label: str,
    *,
    bounds: tuple[float, float, float, float] = (0.765, 0.205, 0.17, 0.17),
    colors: Mapping[str, str] | None = None,
    **axes_kwargs: Any,
) -> plt.Axes:
    """Create and draw a reusable globe inset, returning its Matplotlib axes."""
    ax = figure.add_axes(bounds, facecolor="none", **axes_kwargs)
    draw_globe(ax, world, brazil_ibge, label=label, colors=colors)
    return ax
