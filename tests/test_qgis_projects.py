import xml.etree.ElementTree as ET
from pathlib import Path

import geopandas as gpd
import rasterio
from shapely.geometry import box

from make_a_map.qgis_projects import _square_bounds, _write_project, _write_projected_relief


def test_qgis_project_is_relative_and_keeps_state_boundaries_on_top(tmp_path: Path) -> None:
    frame = gpd.GeoDataFrame(geometry=[box(0, 0, 10, 10)], crs="EPSG:5880")
    layers = [
        ("state_boundaries", frame, "#4A4A4A"),
        ("amazon_biome", frame, "#285943"),
        ("states_context", frame, "#DEDEDE"),
    ]
    project = tmp_path / "map.qgs"

    _write_project(project, "map", layers)

    text = project.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    tree_layers = root.findall("./layer-tree-group/layer-tree-layer")
    assert tree_layers[0].attrib["name"] == "state_boundaries"
    assert tree_layers[-1].attrib["name"] == "shaded_relief"
    assert tree_layers[-1].attrib["source"] == "./relief.tif"
    assert all(
        layer.attrib["source"].startswith("./layers.gpkg") for layer in tree_layers[:-1]
    )
    assert str(Path.cwd()) not in text
    assert "Paths><Absolute type=\"bool\">false" in text
    assert root.find("./mapcanvas/extent") is not None
    symbol_options = root.findall(
        ".//renderer-v2/symbols/symbol/layer/Option[@type='Map']/Option"
    )
    colors = {
        option.attrib["value"]
        for option in symbol_options
        if option.attrib.get("name") == "color"
    }
    assert "40,89,67,255" in colors
    assert "222,222,222,255" in colors
    assert all(not color.startswith("#") for color in colors)


def test_projected_relief_uses_shared_crs_and_square_bounds(tmp_path: Path) -> None:
    source = tmp_path / "source.tif"
    target = tmp_path / "target.tif"
    data = __import__("numpy").full((10, 10), 128, dtype="uint8")
    with rasterio.open(
        source,
        "w",
        driver="GTiff",
        width=10,
        height=10,
        count=1,
        dtype="uint8",
        crs="EPSG:4326",
        transform=rasterio.transform.from_bounds(-70, -20, -40, 10, 10, 10),
    ) as dataset:
        dataset.write(data, 1)
    frame = gpd.GeoDataFrame(geometry=[box(3_000_000, 7_000_000, 5_000_000, 8_000_000)], crs="EPSG:5880")
    bounds = _square_bounds(frame, padding_ratio=0.03)

    _write_projected_relief(source, target, bounds)

    with rasterio.open(target) as dataset:
        assert dataset.crs.to_epsg() == 5880
        assert dataset.width == dataset.height == 2250
        assert tuple(dataset.bounds) == bounds
