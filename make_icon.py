#!/usr/bin/env python3
"""Generate placeholder app icons (icon.png + icon.ico).

Run once before building. The output files are picked up by build.py.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).parent.resolve()


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pad = size // 16
    d.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=size // 6,
        fill=(33, 118, 197, 255),
    )

    fpad = size // 5
    top = fpad + size // 14
    bottom = size - fpad
    left = fpad
    right = size - fpad
    d.rounded_rectangle(
        [(left, top), (right, bottom)],
        radius=size // 24,
        fill=(255, 255, 255, 255),
    )

    sun_r = size // 14
    sun_c = (left + (right - left) // 4, top + (bottom - top) // 3)
    d.ellipse(
        [
            (sun_c[0] - sun_r, sun_c[1] - sun_r),
            (sun_c[0] + sun_r, sun_c[1] + sun_r),
        ],
        fill=(255, 193, 7, 255),
    )

    base_y = bottom - size // 32
    peak1 = (left + (right - left) // 2 - size // 24, top + (bottom - top) // 3)
    peak2 = (left + (right - left) * 5 // 8, top + (bottom - top) // 2)
    d.polygon(
        [
            (left + size // 24, base_y),
            peak1,
            (left + (right - left) * 5 // 8, base_y),
        ],
        fill=(40, 120, 60, 255),
    )
    d.polygon(
        [
            (left + (right - left) // 2, base_y),
            peak2,
            (right - size // 32, base_y),
        ],
        fill=(70, 90, 110, 255),
    )

    return img


def main() -> int:
    big = draw_icon(1024)
    png_path = ROOT / "icon.png"
    big.save(png_path, format="PNG")
    print(f"wrote {png_path}")

    sizes = [16, 32, 48, 64, 128, 256]
    ico_path = ROOT / "icon.ico"
    big.save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
    )
    print(f"wrote {ico_path} (sizes: {sizes})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
