import pytest

from make_a_map.layout import Box, get_layout
from make_a_map.maps.legal_amazon import create_spec


def test_layout_slots_stay_inside_square_and_validate() -> None:
    layout = get_layout("map-plus-metric")
    layout.validate()
    assert layout.map_body.width * layout.map_body.height > layout.globe.width * layout.globe.height


def test_box_overlap_is_detected() -> None:
    assert Box(0, 0, 0.5, 0.5).overlaps(Box(0.25, 0.25, 0.5, 0.5))
    assert not Box(0, 0, 0.5, 0.5).overlaps(Box(0.5, 0, 0.5, 0.5))


def test_legal_amazon_spec_has_atomic_bilingual_output_contract() -> None:
    spec = create_spec()
    assert spec.layout.pixel_size == (2250, 2250)
    assert spec.output_name("pt-BR", "png") == "legal-amazon_pt-BR.png"
    assert spec.output_name("en-US", "svg") == "legal-amazon_en-US.svg"


def test_scientific_and_editorial_modes_are_explicit() -> None:
    assert create_spec("scientific").mode == "scientific"
    assert create_spec("editorial").mode == "editorial"


def test_unknown_mode_fails() -> None:
    with pytest.raises(ValueError, match="mode"):
        create_spec("promotional")
