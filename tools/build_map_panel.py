"""Build one contact panel from the six approved Portuguese map masters."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
TARGET = OUTPUTS / "painel-todos-os-mapas.png"

MAPS = (
    ("amazon-cerrado-biomes", "Amazônia e Cerrado"),
    ("amazon-biome", "Bioma Amazônia"),
    ("cerrado-biome", "Bioma Cerrado"),
    ("sao-felix-do-xingu", "São Félix do Xingu"),
    ("sao-felix-do-xingu-car-property", "Imóvel rural sintético"),
    ("sao-felix-do-xingu-purchasing-zone", "Zona de compra sintética"),
)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def build_panel() -> Path:
    """Compose the masters without changing their internal cartography."""
    columns = 3
    rows = 2
    tile_size = 900
    title_height = 78
    gutter = 34
    margin = 44
    width = margin * 2 + columns * tile_size + (columns - 1) * gutter
    height = margin * 2 + rows * (title_height + tile_size) + (rows - 1) * gutter
    panel = Image.new("RGB", (width, height), "#E8E8E5")
    draw = ImageDraw.Draw(panel)
    font = _font(30)

    for index, (slug, title) in enumerate(MAPS):
        source = OUTPUTS / slug / "latest" / f"{slug}_pt-BR.png"
        if not source.is_file():
            raise FileNotFoundError(source)
        column = index % columns
        row = index // columns
        x = margin + column * (tile_size + gutter)
        y = margin + row * (tile_size + title_height + gutter)
        bounds = draw.textbbox((0, 0), title, font=font)
        text_width = bounds[2] - bounds[0]
        draw.text(
            (x + (tile_size - text_width) / 2, y + 18),
            title,
            fill="#303735",
            font=font,
        )
        with Image.open(source) as master:
            tile = master.convert("RGB").resize(
                (tile_size, tile_size), Image.Resampling.LANCZOS
            )
        panel.paste(tile, (x, y + title_height))

    panel.save(TARGET, format="PNG", dpi=(300, 300), optimize=True)
    return TARGET


if __name__ == "__main__":
    print(build_panel())
