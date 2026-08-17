"""Validate QGIS projects with the native QGIS runtime."""

from __future__ import annotations

import sys
from pathlib import Path

from qgis.core import (
    QgsApplication,
    QgsMapRendererParallelJob,
    QgsMapSettings,
    QgsProject,
)
from qgis.PyQt.QtCore import QSize


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    application = QgsApplication([], False)
    application.initQgis()
    try:
        projects = sorted(root.glob("*/qgis/*.qgs"))
        assert len(projects) == 6
        for path in projects:
            project = QgsProject.instance()
            project.clear()
            assert project.read(str(path))
            assert project.backgroundColor().name() == "#ccd3d5"
            layouts = {layout.name(): layout for layout in project.layoutManager().layouts()}
            assert set(layouts) == {"pt-BR", "en-US"}, (path, layouts)
            for layout in layouts.values():
                size = layout.pageCollection().page(0).pageSize()
                assert abs(size.width() - 190.5) < 0.01
                assert abs(size.height() - 190.5) < 0.01
                assert len(layout.items()) >= 2
            vector_layers = [layer for layer in project.mapLayers().values() if layer.type() == 0]
            assert vector_layers
            assert all(layer.renderer() is not None for layer in vector_layers)
            relief = next(layer for layer in project.mapLayers().values() if layer.name() == "shaded_relief")
            assert abs(relief.opacity() - 0.10) < 0.001
            referenced_extent = project.viewSettings().defaultViewExtent()
            assert not referenced_extent.isNull() and not referenced_extent.isEmpty()
            extent = referenced_extent
            assert abs(extent.width() - extent.height()) < 0.01
            settings = QgsMapSettings()
            settings.setLayers(list(project.mapLayers().values()))
            settings.setDestinationCrs(project.crs())
            settings.setExtent(extent)
            settings.setOutputSize(QSize(400, 400))
            job = QgsMapRendererParallelJob(settings)
            job.start()
            job.waitForFinished()
            image = job.renderedImage()
            assert not image.isNull()
            colors = {
                image.pixelColor(x, y).name()
                for x in range(0, image.width(), 20)
                for y in range(0, image.height(), 20)
            }
            assert len(colors) > 3, (path, colors)
            states_context = next(
                (layer for layer in vector_layers if layer.name() == "states_context"),
                None,
            )
            if states_context is not None:
                assert states_context.labelsEnabled()
                assert states_context.labeling().settings().isExpression
            print(
                f"{path}: 2 layouts, {len(vector_layers)} styled vector layers, "
                f"rendered canvas"
            )
    finally:
        application.exitQgis()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
