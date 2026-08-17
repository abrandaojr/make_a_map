"""Create portable QGIS projects for the six-map requested series."""

from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject

from .maps.requested_series import (
    AMAZON_COLOR,
    CERRADO_COLOR,
    CONSERVATION_COLOR,
    DISPLAY_CRS,
    INDIGENOUS_COLOR,
    INK,
    PAPER,
    ROOT,
    SERIES,
    THEME,
    _load,
    _synthetic_property,
)


def _project_layers(slug: str, source: dict[str, gpd.GeoDataFrame]) -> list[tuple[str, gpd.GeoDataFrame, str]]:
    """Return layers in QGIS top-to-bottom drawing order."""
    state_boundaries = source["states"].copy()
    layers: list[tuple[str, gpd.GeoDataFrame, str]] = [("state_boundaries", state_boundaries, INK)]
    if slug in {"amazon-biome", "cerrado-biome", "amazon-cerrado-biomes"}:
        amazon = source["biomes"].loc[source["biomes"].NM_BIOMA == "Amazônia"].copy()
        cerrado = source["biomes"].loc[source["biomes"].NM_BIOMA == "Cerrado"].copy()
        if slug in {"amazon-biome", "amazon-cerrado-biomes"}:
            layers.append(("amazon_biome", amazon, AMAZON_COLOR))
        if slug in {"cerrado-biome", "amazon-cerrado-biomes"}:
            layers.append(("cerrado_biome", cerrado, CERRADO_COLOR))
        layers.insert(1, ("major_cities", source["cities"].copy(), "#4B5350"))
        layers.append(("states_context", source["states"].copy(), "#E1E0DB"))
        layers.append(("world_land", source["world_display"].copy(), "#E1E0DB"))
        return layers

    municipality = source["sao_felix"].copy()
    osm = source["osm"].clip(municipality.geometry.union_all())
    layers.append(("municipality_boundary", municipality, "#87908B"))
    layers.append(("osm_major_roads", osm.loc[osm.highway.isin(["primary", "secondary"])], "#E8E8E8"))
    layers.append(("osm_tertiary_roads", osm.loc[osm.highway == "tertiary"], "#E2E2E2"))
    layers.append(("osm_rivers", osm.loc[osm.waterway == "river"], "#B8B8B8"))
    if slug == "sao-felix-do-xingu":
        protected_units = source["conservation_units"].clip(municipality.geometry.union_all())
        protected_lands = source["indigenous_lands"].clip(municipality.geometry.union_all())
        layers.append(("protected_indigenous_lands", protected_lands, INDIGENOUS_COLOR))
        layers.append(("protected_conservation_units", protected_units, CONSERVATION_COLOR))
    if slug == "sao-felix-do-xingu-car-property":
        layers.append(("synthetic_car_property", _synthetic_property(municipality), THEME))
    elif slug == "sao-felix-do-xingu-purchasing-zone":
        center = municipality.geometry.union_all().representative_point()
        zone = gpd.GeoDataFrame(
            geometry=[center.buffer(40_000).intersection(municipality.geometry.union_all())],
            crs=municipality.crs,
        )
        layers.append(("synthetic_purchasing_zone_40_km", zone, THEME))
    else:
        layers.append(("sao_felix_do_xingu", municipality, "#A6A6A3"))
    layers.append(("neighboring_municipalities", source["neighbors"].copy(), "#E1E0DB"))
    return layers


def _maplayer(layer_id: str, name: str, color: str, extent: tuple[float, float, float, float]) -> ET.Element:
    minx, miny, maxx, maxy = extent
    point_layer = name == "major_cities"
    line_layer = name == "municipality_boundary" or name.startswith("osm_")
    geometry_type = "Point" if point_layer else "Line" if line_layer else "Polygon"
    layer = ET.Element("maplayer", type="vector", geometry=geometry_type, simplifyDrawingHints="1")
    ET.SubElement(layer, "id").text = layer_id
    ET.SubElement(layer, "datasource").text = f"./layers.gpkg|layername={name}"
    ET.SubElement(layer, "layername").text = name
    ET.SubElement(layer, "provider", encoding="UTF-8").text = "ogr"
    extent_node = ET.SubElement(layer, "extent")
    for key, value in (("xmin", minx), ("ymin", miny), ("xmax", maxx), ("ymax", maxy)):
        ET.SubElement(extent_node, key).text = str(value)
    renderer = ET.SubElement(layer, "renderer-v2", type="singleSymbol", symbollevels="0")
    symbols = ET.SubElement(renderer, "symbols")
    symbol_type = "marker" if point_layer else "line" if line_layer else "fill"
    symbol = ET.SubElement(symbols, "symbol", name="0", type=symbol_type, alpha="1")
    symbol_class = "SimpleMarker" if point_layer else "SimpleLine" if line_layer else "SimpleFill"
    symbol_layer = ET.SubElement(
        symbol,
        "layer",
        **{"class": symbol_class, "enabled": "1", "locked": "0", "pass": "0"},
    )

    def qgis_color(hex_color: str) -> str:
        """Convert a CSS hex color to the RGBA value expected by QGIS symbols."""
        red, green, blue = (
            int(hex_color[index : index + 2], 16) for index in (1, 3, 5)
        )
        return f"{red},{green},{blue},255"

    options = (
        (("color", qgis_color(color)), ("outline_color", qgis_color(PAPER)), ("size", "1.8"))
        if point_layer
        else (("line_color", qgis_color(color)), ("line_width", "0.35"))
        if line_layer
        else (
            ("color", qgis_color(color)),
            ("outline_color", qgis_color(INK if name != "states_context" else "#FFFFFF")),
            ("outline_width", "0.6" if name == "state_boundaries" else "0.25"),
            ("style", "no" if name == "state_boundaries" else "solid"),
        )
    )
    option_map = ET.SubElement(symbol_layer, "Option", type="Map")
    for key, value in options:
        ET.SubElement(option_map, "Option", name=key, value=value, type="QString")
    return layer


def _write_project(path: Path, slug: str, layers: list[tuple[str, gpd.GeoDataFrame, str]]) -> None:
    project = ET.Element("qgis", version="3.34.0", projectname=slug)
    title = ET.SubElement(project, "title")
    title.text = slug
    project_crs = ET.SubElement(project, "projectCrs")
    spatial_reference = ET.SubElement(project_crs, "spatialrefsys")
    ET.SubElement(spatial_reference, "authid").text = DISPLAY_CRS
    ET.SubElement(spatial_reference, "description").text = "SIRGAS 2000 / Brazil Polyconic"
    ET.SubElement(spatial_reference, "projectionacronym").text = "poly"
    ET.SubElement(spatial_reference, "ellipsoidacronym").text = "GRS80"
    layer_names = {item[0] for item in layers}
    if "municipality_boundary" in layer_names:
        view_frames = [frame for name, frame, _ in layers if name == "municipality_boundary"]
        padding_ratio = 0.012
    else:
        view_frames = [frame for name, frame, _ in layers if name == "states_context"]
        padding_ratio = 0.03
    bounds = [frame.total_bounds for frame in view_frames]
    minx = min(item[0] for item in bounds)
    miny = min(item[1] for item in bounds)
    maxx = max(item[2] for item in bounds)
    maxy = max(item[3] for item in bounds)
    padding = max(maxx - minx, maxy - miny) * padding_ratio
    map_canvas = ET.SubElement(project, "mapcanvas", name="theMapCanvas", annotationsVisible="1")
    canvas_extent = ET.SubElement(map_canvas, "extent")
    for key, value in (
        ("xmin", minx - padding),
        ("ymin", miny - padding),
        ("xmax", maxx + padding),
        ("ymax", maxy + padding),
    ):
        ET.SubElement(canvas_extent, key).text = str(value)
    destination_crs = ET.SubElement(map_canvas, "destinationsrs")
    destination_crs.append(ET.fromstring(ET.tostring(spatial_reference, encoding="unicode")))
    tree = ET.SubElement(project, "layer-tree-group", name="", checked="Qt::Checked", expanded="1")
    project_layers = ET.SubElement(project, "projectlayers")
    order = ET.SubElement(ET.SubElement(project, "layer-tree-canvas"), "custom-order", enabled="1")
    for index, (name, frame, color) in enumerate(layers):
        layer_id = f"{slug}_{name}_{index}"
        ET.SubElement(
            tree,
            "layer-tree-layer",
            id=layer_id,
            name=name,
            source=f"./layers.gpkg|layername={name}",
            providerKey="ogr",
            checked="Qt::Checked",
            expanded="1",
        )
        ET.SubElement(order, "item").text = layer_id
        project_layers.append(_maplayer(layer_id, name, color, tuple(frame.total_bounds)))
    relief_id = f"{slug}_shaded_relief"
    ET.SubElement(
        tree,
        "layer-tree-layer",
        id=relief_id,
        name="shaded_relief",
        source="./relief.tif",
        providerKey="gdal",
        checked="Qt::Checked",
        expanded="1",
    )
    ET.SubElement(order, "item").text = relief_id
    relief_layer = ET.SubElement(project_layers, "maplayer", type="raster", opacity="0.15")
    ET.SubElement(relief_layer, "id").text = relief_id
    ET.SubElement(relief_layer, "datasource").text = "./relief.tif"
    ET.SubElement(relief_layer, "layername").text = "shaded_relief"
    ET.SubElement(relief_layer, "provider").text = "gdal"
    pipe = ET.SubElement(relief_layer, "pipe")
    renderer = ET.SubElement(
        pipe, "rasterrenderer", type="singlebandgray", grayBand="1", opacity="0.15"
    )
    ET.SubElement(renderer, "rasterTransparency")
    properties = ET.SubElement(project, "properties")
    paths = ET.SubElement(properties, "Paths")
    ET.SubElement(paths, "Absolute", type="bool").text = "false"
    ET.ElementTree(project).write(path, encoding="UTF-8", xml_declaration=True)


def _square_bounds(
    frame: gpd.GeoDataFrame, *, padding_ratio: float
) -> tuple[float, float, float, float]:
    """Return the exact square map bounds in the shared display CRS."""
    minx, miny, maxx, maxy = frame.total_bounds
    center_x = (minx + maxx) / 2
    center_y = (miny + maxy) / 2
    span = max(maxx - minx, maxy - miny) * (1 + 2 * padding_ratio)
    return (
        center_x - span / 2,
        center_y - span / 2,
        center_x + span / 2,
        center_y + span / 2,
    )


def _write_projected_relief(
    source_path: Path,
    target_path: Path,
    bounds: tuple[float, float, float, float],
) -> None:
    """Physically warp the relief to EPSG:5880 and the packaged map extent."""
    size = 2250
    destination = np.zeros((size, size), dtype=np.uint8)
    transform = from_bounds(*bounds, size, size)
    with rasterio.open(source_path) as source:
        reproject(
            source=rasterio.band(source, 1),
            destination=destination,
            src_transform=source.transform,
            src_crs=source.crs,
            dst_transform=transform,
            dst_crs=DISPLAY_CRS,
            resampling=Resampling.bilinear,
            dst_nodata=0,
        )
    with rasterio.open(
        target_path,
        "w",
        driver="GTiff",
        width=size,
        height=size,
        count=1,
        dtype=destination.dtype,
        crs=DISPLAY_CRS,
        transform=transform,
        nodata=0,
        compress="deflate",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as target:
        target.write(destination, 1)


def build_qgis_projects(output_root: Path | None = None, *, offline: bool = False) -> Path:
    """Write one self-contained QGIS folder beside each published map bundle."""
    output_root = output_root or ROOT / "outputs"
    source, _ = _load(offline)
    for slug in SERIES:
        target = output_root / slug / "qgis"
        staging = output_root / slug / ".qgis-staging"
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        layers = _project_layers(slug, source)
        package = staging / "layers.gpkg"
        for name, frame, _ in reversed(layers):
            frame.to_file(package, layer=name, driver="GPKG")
        local = "municipality_boundary" in {name for name, _, _ in layers}
        context_name = "municipality_boundary" if local else "states_context"
        context = next(frame for name, frame, _ in layers if name == context_name)
        relief_bounds = _square_bounds(context, padding_ratio=0.012 if local else 0.03)
        _write_projected_relief(source["relief"], staging / "relief.tif", relief_bounds)
        _write_project(staging / f"{slug}.qgs", slug, layers)
        (staging / "README.txt").write_text(
            "Open the .qgs file in QGIS 3.34 or newer. All paths are relative.\n"
            "All vector and raster layers are physically stored in EPSG:5880.\n"
            "State boundaries are the top layer; shaded relief is the bottom layer.\n"
            "Run tools/finalize_qgis_projects.py to add the pt-BR and en-US print layouts.\n"
            "The finalized layouts reproduce the approved 7.5-inch masters.\n"
            "CAR and purchasing-zone geometries are synthetic.\n"
            "OpenStreetMap linework: © OpenStreetMap contributors (ODbL 1.0).\n",
            encoding="utf-8",
        )
        if target.exists():
            shutil.rmtree(target)
        staging.replace(target)
    return output_root
