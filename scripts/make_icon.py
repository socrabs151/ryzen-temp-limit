from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

SCALE = 4
SIZE = 256
CANVAS = SIZE * SCALE
ASSETS = Path(__file__).resolve().parent.parent / "ryzen_temp_limit" / "assets"

BG = "#0f1216"
PANEL = "#161b22"
STEM_OUTER = "#2b3440"
STEM_INNER = "#0f1216"
ACCENT = "#ff7a18"
ACCENT_DIM = "#7a3f12"
TICK = "#3a4552"
WHITE = "#e8eef5"


def draw_icon() -> Image.Image:
    image = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    radius = int(CANVAS * 0.22)
    draw.rounded_rectangle((0, 0, CANVAS - 1, CANVAS - 1), radius=radius, fill=BG, outline=STEM_OUTER, width=SCALE * 2)

    cx = CANVAS // 2
    stem_w = int(CANVAS * 0.16)
    stem_top = int(CANVAS * 0.17)
    bulb_cy = int(CANVAS * 0.71)
    bulb_r = int(CANVAS * 0.135)
    stem_bottom = bulb_cy

    outer = stem_w // 2 + SCALE * 3
    draw.rounded_rectangle(
        (cx - outer, stem_top - SCALE * 3, cx + outer, stem_bottom + SCALE * 3),
        radius=outer,
        fill=STEM_OUTER,
    )
    draw.ellipse(
        (cx - bulb_r - SCALE * 3, bulb_cy - bulb_r - SCALE * 3,
         cx + bulb_r + SCALE * 3, bulb_cy + bulb_r + SCALE * 3),
        fill=STEM_OUTER,
    )

    inner = stem_w // 2
    draw.rounded_rectangle(
        (cx - inner, stem_top, cx + inner, stem_bottom),
        radius=inner,
        fill=STEM_INNER,
    )
    draw.ellipse(
        (cx - bulb_r, bulb_cy - bulb_r, cx + bulb_r, bulb_cy + bulb_r),
        fill=STEM_INNER,
    )

    fill_top = int(CANVAS * 0.40)
    draw.rounded_rectangle(
        (cx - inner + SCALE * 2, fill_top, cx + inner - SCALE * 2, stem_bottom + inner),
        radius=inner,
        fill=ACCENT,
    )
    draw.ellipse(
        (cx - bulb_r + SCALE * 2, bulb_cy - bulb_r + SCALE * 2,
         cx + bulb_r - SCALE * 2, bulb_cy + bulb_r - SCALE * 2),
        fill=ACCENT,
    )

    for offset in (0.00, 0.11, 0.22):
        y = fill_top + int(CANVAS * offset) - SCALE * 6
        draw.rounded_rectangle(
            (cx - int(CANVAS * 0.30), y, cx - int(CANVAS * 0.24), y + SCALE * 4),
            radius=SCALE * 2,
            fill=TICK,
        )

    marker_y = fill_top - SCALE * 2
    draw.rounded_rectangle(
        (cx - int(CANVAS * 0.33), marker_y, cx + int(CANVAS * 0.33), marker_y + SCALE * 5),
        radius=SCALE * 2,
        fill=WHITE,
    )

    return image.resize((SIZE, SIZE), Image.LANCZOS)


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    icon = draw_icon()
    icon.save(ASSETS / "icon.png")
    icon.save(
        ASSETS / "icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"Wrote {ASSETS / 'icon.ico'}")


if __name__ == "__main__":
    main()
