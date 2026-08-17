"""Command-line interface for the final map collection."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .maps.biome_variations import build_biome_variations
from .maps.requested_series import build_requested_series
from .qgis_projects import build_qgis_projects


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="make-a-map", description="Build the final bilingual Brazil map collection"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for command, help_text in (
        ("build", "build the six final bilingual maps"),
        ("qgis", "build the six portable QGIS projects"),
    ):
        item = commands.add_parser(command, help=help_text)
        item.add_argument("--offline", action="store_true")
        item.add_argument("--output", type=Path, default=Path("outputs"))
    variations = commands.add_parser(
        "variations", help="build ten bilingual Amazon and Cerrado visual studies"
    )
    variations.add_argument("--output", type=Path, default=Path("outputs"))
    commands.add_parser("doctor", help="check runtime dependencies and final catalogs")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build":
        print(build_requested_series(args.output, offline=args.offline))
        return 0
    if args.command == "qgis":
        print(build_qgis_projects(args.output, offline=args.offline))
        return 0
    if args.command == "variations":
        print(build_biome_variations(args.output))
        return 0
    if args.command == "doctor":
        try:
            import geopandas
            import matplotlib
            import pyproj
            import shapely

            from .data import load_catalog
            from .maps.requested_series import MUNICIPALITY_GEOCODES_PATH, SERIES

            sources = load_catalog()
            if not MUNICIPALITY_GEOCODES_PATH.is_file():
                raise FileNotFoundError(MUNICIPALITY_GEOCODES_PATH)
        except (ImportError, OSError, ValueError) as error:
            print(f"doctor failed: {error}", file=sys.stderr)
            return 2
        print(f"Python {sys.version.split()[0]}")
        print(f"GeoPandas {geopandas.__version__}; Matplotlib {matplotlib.__version__}")
        print(f"PROJ {pyproj.proj_version_str}; Shapely {shapely.__version__}")
        print(f"Final collection: {len(SERIES)} maps; {len(sources)} sources")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
