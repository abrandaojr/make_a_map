# Contributing

The repository contains only the active six-map collection. Run these commands before
submitting a change:

```bash
make doctor
make build OFFLINE=1
make qgis OFFLINE=1
make check
```

When the native QGIS Python environment is available, also run:

```bash
make qgis-finalize qgis-validate
```

The finalization step adds the `pt-BR` and `en-US` print layouts. The validation step
opens and renders all six projects through QGIS; neither command uses the project
virtual environment.

Inspect both language PNGs for every changed map. Confirm that:

- the canvas is 7.5 × 7.5 inches at 300 dpi;
- all context uses neutral gray tones, with no black elements;
- shaded relief remains subtle and does not compete with thematic fills;
- only the primary map subject uses color;
- state boundaries are visible above every thematic layer;
- national city labels use official IBGE localities and remain collision-free;
- the globe has no unexplained point marker;
- Portuguese and English use identical geometry and values;
- synthetic CAR and purchasing-zone layers contain no identifying information;
- each manifest records source editions, SHA-256 hashes, CRS, and review status;
- each QGIS project uses only relative paths.
