from make_a_map.maps.biome_variations import COLLECTION_SLUG, VARIATIONS


def test_collection_has_ten_distinct_bilingual_visual_studies() -> None:
    assert COLLECTION_SLUG == "amazon-cerrado-variations"
    assert len(VARIATIONS) == 10
    assert len({item.slug for item in VARIATIONS}) == 10
    assert len({(item.amazon, item.cerrado, item.land, item.ocean) for item in VARIATIONS}) == 10
    assert all(item.name_pt and item.name_en for item in VARIATIONS)


def test_every_variation_keeps_themes_distinguishable() -> None:
    for item in VARIATIONS:
        assert item.amazon != item.cerrado
        assert 0 <= item.relief_alpha <= 1
        assert 0 <= item.fill_alpha <= 1


def test_flat_collection_filenames_include_the_version() -> None:
    for item in VARIATIONS:
        assert f"amazon-cerrado-{item.slug}_pt-BR.png" != (
            f"amazon-cerrado-{item.slug}_en-US.png"
        )
        assert f"manifest-{item.slug}.json".startswith("manifest-version-")
