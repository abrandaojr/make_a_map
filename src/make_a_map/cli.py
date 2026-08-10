"""Stable command-line surface for authors and reviewers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .maps.legal_amazon import build as build_legal_amazon
from .recipes import list_recipes, scaffold_recipe


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="make-a-map", description="Bilingual editorial cartography for Brazil"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("templates", help="list versioned map recipes")
    new = sub.add_parser("new", help="scaffold a map project from a recipe")
    new.add_argument("slug")
    new.add_argument("--template", required=True)
    new.add_argument("--directory", type=Path, default=Path("map-projects"))
    build = sub.add_parser("build", help="build a governed bilingual map")
    build.add_argument("map", choices=("legal-amazon",))
    build.add_argument("--offline", action="store_true")
    build.add_argument("--mode", choices=("editorial", "scientific"), default="editorial")
    build.add_argument("--output", type=Path, default=Path("outputs"))
    sub.add_parser("doctor", help="check runtime dependencies and recipe catalog")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "templates":
        for recipe in list_recipes():
            print(f"{recipe.slug:34} {recipe.maturity:12} {recipe.kind}")
        return 0
    if args.command == "new":
        project_dir = args.directory / args.slug
        project_dir.mkdir(parents=True, exist_ok=False)
        destination = project_dir / "map.json"
        payload = scaffold_recipe(args.template)
        payload["slug"] = args.slug
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(destination)
        return 0
    if args.command == "build":
        destination = build_legal_amazon(args.output, offline=args.offline, mode=args.mode)
        print(destination)
        return 0
    if args.command == "doctor":
        try:
            import geopandas
            import matplotlib
            import pyproj
            import shapely

            recipes = list_recipes()
        except (ImportError, OSError, ValueError) as error:
            print(f"doctor failed: {error}", file=sys.stderr)
            return 2
        print(f"Python {sys.version.split()[0]}")
        print(f"GeoPandas {geopandas.__version__}; Matplotlib {matplotlib.__version__}")
        print(f"PROJ {pyproj.proj_version_str}; Shapely {shapely.__version__}")
        print(f"Recipes: {len(recipes)}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
