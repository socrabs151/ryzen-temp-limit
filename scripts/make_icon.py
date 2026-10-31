from __future__ import annotations

import io
import math
import struct
from pathlib import Path

from PIL import Image, ImageDraw

ORANGE = (255, 90, 31, 255)
PEACH = (255, 201, 176, 255)
TICK = (255, 240, 230, 210)

ASSETS = Path(__file__).resolve().parent.parent / "ryzen_temp_limit" / "assets"
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def render(size: int) -> Image.Image:
    level = "small" if size <= 23 else ("medium" if size < 48 else "large")
    scale = 8 if size <= 64 else 4
    s = size * scale
    image = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    cx, cy = s * 0.5, s * 0.585
    radius = s * 0.415
    if level == "small":
        width = s * 0.20
    elif level == "medium":
        width = s * 0.155
    else:
        width = s * 0.118

    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    start, end = 150, 390
    hot = start + (80 - 40) / 65 * (end - start)

    draw.arc(box, start=start, end=hot, fill=ORANGE, width=int(width))
    draw.arc(box, start=hot, end=end, fill=PEACH, width=int(width))
    for angle, color in ((start, ORANGE), (end, PEACH)):
        a = math.radians(angle)
        ex = cx + (radius - width / 2) * math.cos(a)
        ey = cy + (radius - width / 2) * math.sin(a)
        r = width / 2
        draw.ellipse((ex - r, ey - r, ex + r, ey + r), fill=color)

    if level != "small":
        for value in range(40, 106, 10):
            a = math.radians(start + (value - 40) / 65 * (end - start))
            inner = radius - width * 0.86
            outer = radius - width * 0.16
            draw.line(
                (cx + inner * math.cos(a), cy + inner * math.sin(a),
                 cx + outer * math.cos(a), cy + outer * math.sin(a)),
                fill=TICK,
                width=max(2, int(s * 0.012)),
            )

    a = math.radians(start + (78 - 40) / 65 * (end - start))
    needle_len = radius - width * 0.42
    needle_w = s * (0.075 if level == "small" else (0.05 if level == "medium" else 0.032))
    draw.line(
        (cx, cy, cx + needle_len * math.cos(a), cy + needle_len * math.sin(a)),
        fill=ORANGE,
        width=int(needle_w),
    )
    if level == "small":
        hub = s * 0.13
        draw.ellipse((cx - hub, cy - hub, cx + hub, cy + hub), fill=PEACH)
    else:
        hub = s * (0.105 if level == "medium" else 0.082)
        draw.ellipse((cx - hub, cy - hub, cx + hub, cy + hub), fill=PEACH)
        inner = hub * 0.42
        draw.ellipse((cx - inner, cy - inner, cx + inner, cy + inner), fill=ORANGE)

    return image.resize((size, size), Image.LANCZOS)


def write_ico(path: Path, sizes: list[int]) -> None:
    images = [(size, render(size)) for size in sizes]
    payloads: list[bytes] = []
    for _, image in images:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        payloads.append(buffer.getvalue())

    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b""
    for (size, _), payload in zip(images, payloads, strict=True):
        entries += struct.pack(
            "<BBBBHHII",
            0 if size >= 256 else size,
            0 if size >= 256 else size,
            0, 0, 1, 32,
            len(payload),
            offset,
        )
        offset += len(payload)
    path.write_bytes(header + entries + b"".join(payloads))


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    render(512).save(ASSETS / "icon.png")
    write_ico(ASSETS / "icon.ico", ICO_SIZES)
    print(f"Wrote {ASSETS / 'icon.ico'}")


if __name__ == "__main__":
    main()
