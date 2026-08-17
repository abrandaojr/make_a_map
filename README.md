# Make a Map

Make a Map builds one final collection of six bilingual maps of Brazil. Every master is
7.5 × 7.5 inches at 300 dpi and is generated in Brazilian Portuguese (`pt-BR`) and
American English (`en-US`) from the same prepared geometry.

An additional design-study collection provides ten visual versions of the combined
Amazon and Cerrado map. Each version is built in both languages from the same official
IBGE geometry and typed style definition. Run `make variations` to regenerate it under
`outputs/amazon-cerrado-variations/`.

## Final collection

1. Amazon and Cerrado biomes — national overview
2. Amazon biome
3. Cerrado biome
4. São Félix do Xingu
5. Synthetic CAR property in São Félix do Xingu
6. Synthetic purchasing zone in São Félix do Xingu

All maps use the boundary-forward style selected from design study 08, with muted green
for the Amazon, soft ochre for the Cerrado, strong thematic outlines, and subtle shaded
relief. Conservation units and Indigenous lands retain distinct green and burnt-orange
hues in the same restrained palette. State boundaries are always the top drawing layer.
The CAR property and purchasing zone are synthetic and contain no owner, registry, or
supplier identifiers.

Masters are full-bleed 7.5 × 7.5-inch map canvases with no title. A bilingual 16-point
legend at lower left identifies the subject without reserving a separate layout band.

National maps label official IBGE capitals and municipal seats only when scale and
collision spacing permit. Label priority follows the population order of the selected
municipalities, so a larger city suppresses a nearby lower-priority label.
All maps also label visible Brazilian federation units using official IBGE names.

Local maps add an edition-locked OpenStreetMap context selectively by scale: major
roads and rivers at municipality scale, with tertiary roads only in detail views. The
locator globe is fixed at upper right; legends are fixed at lower left. Source records
remain in the manifest rather than competing with the map composition.

## Build

```bash
make setup
make doctor
make build OFFLINE=1
make qgis OFFLINE=1
make check
```

Remove `OFFLINE=1` on the first build if the verified source cache is empty.

`make qgis` creates the portable vector, raster, and base project files. To add the
two approved print layouts and validate the projects with QGIS itself, run
`make qgis-finalize qgis-validate` from a shell whose `python3` provides the native
QGIS bindings. These bindings are distributed with QGIS and are not installed by the
project virtual environment.

## Final structure

```text
data/
  catalog/       Versioned source and municipality catalogs
  cache/         Verified downloads; ignored by Git
docs/             Current contributor guidance
outputs/<map>/
  latest/        Bilingual PNGs, captions, alt text, and manifest
  qgis/          Portable QGIS project and GeoPackage
src/make_a_map/  Active build code only
tests/            Tests for active code only
```

Each QGIS project uses relative `./layers.gpkg` paths and can be moved to another
computer as a complete `qgis/` folder.

Source URLs, editions, expected sizes, and SHA-256 hashes are stored in
[`data/catalog/sources.json`](data/catalog/sources.json). The edition-locked catalog of
5,573 Brazilian municipality geocodes is stored in
[`data/catalog/municipalities.json`](data/catalog/municipalities.json).

See [the contributor guide](docs/CONTRIBUTING.md) for the final review checklist.
