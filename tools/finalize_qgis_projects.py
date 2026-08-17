"""Finalize generated QGIS projects with native styles, labels, and print layouts.

Run this script with the QGIS Python environment after ``make qgis``. The
editable map canvas receives native QGIS renderers and labels. Each project
also receives pt-BR and en-US 7.5-inch print layouts linked to the approved
PNG masters, which guarantees exact visual parity with the published maps.
"""

from __future__ import annotations

import sys
from pathlib import Path

from qgis.core import (
    QgsApplication,
    QgsLayoutItemPicture,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsPalLayerSettings,
    QgsPrintLayout,
    QgsProject,
    QgsRectangle,
    QgsReferencedRectangle,
    QgsSingleSymbolRenderer,
    QgsSymbol,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsUnitTypes,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont

PAGE_MM = 190.5

COLORS = {
    "state_boundaries": "#303735",
    "major_cities": "#4B5350",
    "amazon_biome": "#6F927F",
    "cerrado_biome": "#D8C39B",
    "states_context": "#E1E0DB",
    "world_land": "#E1E0DB",
    "municipality_boundary": "#303735",
    "osm_major_roads": "#E8E8E8",
    "osm_tertiary_roads": "#E2E2E2",
    "osm_rivers": "#B8B8B8",
    "protected_indigenous_lands": "#A56849",
    "protected_conservation_units": "#315C4C",
    "synthetic_car_property": "#6F927F",
    "synthetic_purchasing_zone_40_km": "#6F927F",
    "sao_felix_do_xingu": "#A6A6A3",
    "neighboring_municipalities": "#E1E0DB",
}

POLYGON_OUTLINES = {
    "amazon_biome": 0.55,
    "cerrado_biome": 0.55,
    "protected_indigenous_lands": 0.44,
    "protected_conservation_units": 0.44,
    "synthetic_car_property": 0.55,
    "synthetic_purchasing_zone_40_km": 0.55,
    "sao_felix_do_xingu": 0.55,
}


def _style_layer(layer) -> None:
    color = QColor(COLORS[layer.name()])
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(color)
    symbol_layer = symbol.symbolLayer(0)
    if layer.name() == "state_boundaries":
        symbol_layer.setBrushStyle(Qt.BrushStyle.NoBrush)
        symbol_layer.setStrokeColor(QColor("#303735"))
        symbol_layer.setStrokeWidth(0.17)
    elif layer.geometryType() == 2:
        symbol.setOpacity(0.72 if layer.name() in POLYGON_OUTLINES else 1.0)
        if layer.name() == "world_land":
            symbol_layer.setStrokeStyle(Qt.PenStyle.NoPen)
        else:
            symbol_layer.setStrokeColor(QColor("#303735"))
            symbol_layer.setStrokeWidth(POLYGON_OUTLINES.get(layer.name(), 0.10))
    elif layer.geometryType() == 1:
        symbol_layer.setWidth(0.20)
    elif layer.name() == "major_cities":
        symbol.setSize(1.8)
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))


def _enable_labels(
    layer,
    field: str,
    *,
    italic: bool,
    size: float,
    expression: bool = False,
) -> None:
    settings = QgsPalLayerSettings()
    settings.fieldName = field
    settings.isExpression = expression
    settings.drawLabels = True
    settings.displayAll = False
    settings.priority = 7 if layer.name() == "major_cities" else 5
    text_format = QgsTextFormat()
    font = QFont("Georgia" if italic else "Arial")
    font.setItalic(italic)
    text_format.setFont(font)
    text_format.setSize(size)
    text_format.setColor(QColor("#4B5350"))
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(0.8)
    buffer.setColor(QColor("#F2F2F2"))
    text_format.setBuffer(buffer)
    settings.setFormat(text_format)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)


def _add_master_layout(project: QgsProject, slug: str, locale: str, png: Path) -> None:
    manager = project.layoutManager()
    old = manager.layoutByName(locale)
    if old is not None:
        manager.removeLayout(old)
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(locale)
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(PAGE_MM, PAGE_MM, QgsUnitTypes.LayoutMillimeters))
    picture = QgsLayoutItemPicture(layout)
    picture.setPicturePath(f"../latest/{png.name}")
    picture.attemptMove(QgsLayoutPoint(0, 0, QgsUnitTypes.LayoutMillimeters))
    picture.attemptResize(QgsLayoutSize(PAGE_MM, PAGE_MM, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(picture)
    manager.addLayout(layout)


def finalize(project_path: Path) -> None:
    project = QgsProject.instance()
    project.clear()
    if not project.read(str(project_path.resolve())):
        raise RuntimeError(f"QGIS could not read {project_path}")
    project.setBackgroundColor(QColor("#CCD3D5"))
    for layer in project.mapLayers().values():
        if layer.type() != 0 or layer.name() not in COLORS:
            continue
        _style_layer(layer)
        if layer.name() == "major_cities":
            _enable_labels(layer, "NM_LOCALID", italic=True, size=6.2)
        elif layer.name() == "states_context":
            _enable_labels(
                layer,
                'upper("NM_UF")',
                italic=False,
                size=5.0,
                expression=True,
            )
        elif layer.name() == "neighboring_municipalities":
            _enable_labels(layer, "NM_MUN", italic=True, size=6.3)
    context = next(
        (
            layer
            for layer in project.mapLayers().values()
            if layer.name() in {"states_context", "municipality_boundary"}
        ),
        None,
    )
    if context is None or not context.isValid():
        raise RuntimeError(f"no valid context layer in {project_path}")
    bounds = context.extent()
    center = bounds.center()
    span = max(bounds.width(), bounds.height())
    span *= 1.06 if context.name() == "states_context" else 1.024
    canvas_extent = QgsRectangle(
        center.x() - span / 2,
        center.y() - span / 2,
        center.x() + span / 2,
        center.y() + span / 2,
    )
    project.viewSettings().setDefaultViewExtent(
        QgsReferencedRectangle(canvas_extent, context.crs())
    )
    root = project.layerTreeRoot()
    current_order = root.layerOrder()
    relief = next((layer for layer in current_order if layer.name() == "shaded_relief"), None)
    world = next((layer for layer in current_order if layer.name() == "world_land"), None)
    if relief is not None:
        relief.setOpacity(0.10)
        # Relief must sit over opaque land/context fills, but below themes,
        # linework, points, and labels to match the approved raster masters.
        themes = {
            "amazon_biome",
            "cerrado_biome",
            "protected_indigenous_lands",
            "protected_conservation_units",
            "synthetic_car_property",
            "synthetic_purchasing_zone_40_km",
            "sao_felix_do_xingu",
        }
        thematic_count = sum(layer.name() in themes for layer in current_order)
        reordered = [layer for layer in current_order if layer != relief]
        insert_at = min(len(reordered), 2 + thematic_count)
        reordered.insert(insert_at, relief)
        root.setHasCustomLayerOrder(True)
        root.setCustomLayerOrder(reordered)
    if world is not None:
        world.renderer().symbol().symbolLayer(0).setStrokeStyle(Qt.PenStyle.NoPen)
    slug = project_path.stem
    latest = project_path.parents[1] / "latest"
    for locale in ("pt-BR", "en-US"):
        png = latest / f"{slug}_{locale}.png"
        if not png.is_file():
            raise FileNotFoundError(png)
        _add_master_layout(project, slug, locale, png)
    project.setFileName(str(project_path.resolve()))
    if not project.write():
        raise RuntimeError(f"QGIS could not write {project_path}")


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    application = QgsApplication([], False)
    application.initQgis()
    try:
        projects = sorted(root.glob("*/qgis/*.qgs"))
        if len(projects) != 6:
            raise RuntimeError(f"expected six QGIS projects, found {len(projects)}")
        for project_path in projects:
            finalize(project_path)
            print(project_path)
    finally:
        application.exitQgis()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
