#!/usr/bin/env python3
"""Generate the dedicated Cognitive Logic case-study Open Graph cards."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 1200, 630
BACKGROUND = "#05080B"
PANEL = "#0A0F14"
WHITE = "#F5F3ED"
SOFT_WHITE = "#D8D9D6"
MUTED = "#A9ADB2"
GOLD = "#D6A900"
LINE = "#293039"

SERIF = ROOT / "fonts/cormorant-garamond-normal.woff2"
MONO = ROOT / "fonts/dm-mono-400.woff2"
MONO_MEDIUM = ROOT / "fonts/dm-mono-500.woff2"


CARDS = (
    {
        "path": ROOT / "img/og/coste360-case-study.png",
        "category": "CASE STUDY",
        "title": "Coste360",
        "subtitle": "Evidenze. Assessment. Validazione.",
        "note_1": "Validazione proprietaria Cognitive Logic",
        "note_2": "Non costituisce certificazione indipendente",
        "url": "cognitivelogic.it/case-studies/coste360/",
    },
    {
        "path": ROOT / "img/og/egea-qen-benchmark.png",
        "category": "GOVERNANCE BENCHMARK",
        "title": "Egea–QEN",
        "subtitle": "Sei dimensioni a confronto con QEN",
        "note_1": "Benchmark metodologico e documentale",
        "note_2": "Non costituisce valutazione o certificazione",
        "url": "cognitivelogic.it/case-studies/egea-qen/",
    },
)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def tracked_text(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    spacing: int,
) -> None:
    x, y = position
    for character in text:
        draw.text((x, y), character, font=text_font, fill=fill)
        x += int(draw.textlength(character, font=text_font)) + spacing


def render(card: dict[str, str | Path]) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    # Structural frame and restrained gold accents.
    draw.rectangle((32, 32, WIDTH - 33, HEIGHT - 33), outline=LINE, width=1)
    draw.rectangle((64, 64, 70, 566), fill=GOLD)
    draw.rectangle((92, 515, 1136, 516), fill=LINE)
    draw.rectangle((92, 92, 1136, 93), fill=LINE)
    draw.rectangle((882, 64, 1136, 122), fill=PANEL, outline=LINE, width=1)

    tracked_text(draw, (92, 64), "COGNITIVE LOGIC", font(MONO_MEDIUM, 21), GOLD, 5)

    category = str(card["category"])
    category_font = font(MONO_MEDIUM, 15)
    category_width = draw.textlength(category, font=category_font)
    tracked_text(
        draw,
        (1009 - int(category_width / 2) - (len(category) - 1), 82),
        category,
        category_font,
        WHITE,
        2,
    )

    draw.text((92, 151), str(card["title"]), font=font(SERIF, 91), fill=WHITE)
    draw.rectangle((94, 267, 246, 273), fill=GOLD)
    draw.text((92, 301), str(card["subtitle"]), font=font(MONO_MEDIUM, 27), fill=SOFT_WHITE)

    draw.text((92, 400), str(card["note_1"]), font=font(MONO, 20), fill=WHITE)
    draw.text((92, 437), str(card["note_2"]), font=font(MONO, 18), fill=MUTED)

    tracked_text(draw, (92, 542), str(card["url"]), font(MONO, 16), GOLD, 1)

    output = Path(card["path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True, compress_level=9)


def main() -> None:
    for card in CARDS:
        render(card)


if __name__ == "__main__":
    main()
