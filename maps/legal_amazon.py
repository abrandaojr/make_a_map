"""Backward-compatible entry point for the governed package builder."""

from make_a_map.maps.legal_amazon import build


if __name__ == "__main__":
    print(build())
