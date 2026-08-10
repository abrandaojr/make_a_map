# Make a Map

Reproducible editorial maps of Brazil for scientific papers. Every map is
generated in Brazilian Portuguese (`pt-BR`) and American English (`en-US`).

## First example: Legal Amazon

The example uses the official 2024 Legal Amazon boundary and the matching 2024
state mesh from IBGE. Run:

```bash
make setup
make map
```

Outputs are written to `outputs/` as PNG (300 dpi), PDF and SVG. All figures use
a square 7.5 x 7.5 inch canvas.

## Sources

- IBGE, Legal Amazon boundary, edition 2024.
- IBGE, Digital Municipal Mesh: Federation Units, edition 2024.

The script downloads the raw source archives directly from IBGE and stores them
under `data/raw/`, which is excluded from version control.
