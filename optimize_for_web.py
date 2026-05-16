#!/usr/bin/env python3
"""Generate web-optimized versions of every photo in this folder.

For each source image (JPG/JPEG/PNG/TIFF/WEBP) found next to this script,
the script produces, inside ``./web/``:

  * A "large"  version (max 1920px on the longest side)
  * A "medium" version (max 1200px on the longest side)
  * A "small"  version (max  800px on the longest side)
  * A "thumb"  version (max  400px on the longest side)

Each size is written in two formats: optimized progressive JPEG and WebP.
EXIF orientation is honoured, EXIF metadata is stripped (smaller files,
better for the web), and filenames are slugified (lowercase, no spaces or
``#`` characters) so they are URL-safe.

Usage:
    python3 optimize_for_web.py                    # process current folder
    python3 optimize_for_web.py /path/to/photos    # process another folder
"""

from __future__ import annotations

import argparse
import re
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageOps

SOURCE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}

# (label, max_longest_side_px)
SIZES: list[tuple[str, int]] = [
    ("large", 1920),
    ("medium", 1200),
    ("small", 800),
    ("thumb", 400),
]

JPEG_QUALITY = 82
WEBP_QUALITY = 80


def slugify(name: str) -> str:
    """Make a filename safe and pleasant for the web."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "image"


def resize_keeping_aspect(img: Image.Image, max_side: int) -> Image.Image:
    """Return a copy resized so its longest side equals ``max_side`` (or
    smaller if the source is already small enough).
    """
    w, h = img.size
    longest = max(w, h)
    if longest <= max_side:
        return img.copy()
    scale = max_side / longest
    new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
    return img.resize(new_size, Image.LANCZOS)


def process_one(src: Path, out_dir: Path) -> tuple[str, list[str], str | None]:
    """Generate every variant for a single source file.

    Returns (source_name, list_of_outputs, error_message_or_None).
    """
    try:
        with Image.open(src) as im:
            im.load()
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGB")
            elif im.mode == "RGBA":
                # Flatten transparency onto white for JPEG output.
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1])
                im = bg

            stem = slugify(src.stem)
            outputs: list[str] = []

            for label, max_side in SIZES:
                resized = resize_keeping_aspect(im, max_side)

                jpg_path = out_dir / f"{stem}-{label}.jpg"
                resized.save(
                    jpg_path,
                    format="JPEG",
                    quality=JPEG_QUALITY,
                    optimize=True,
                    progressive=True,
                )
                outputs.append(jpg_path.name)

                webp_path = out_dir / f"{stem}-{label}.webp"
                resized.save(
                    webp_path,
                    format="WEBP",
                    quality=WEBP_QUALITY,
                    method=6,
                )
                outputs.append(webp_path.name)

        return src.name, outputs, None
    except Exception as exc:
        return src.name, [], f"{type(exc).__name__}: {exc}"


def collect_sources(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SOURCE_EXTENSIONS
    )


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="Folder containing the source photos (default: current folder)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="web",
        help="Output subfolder name (default: web)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=0,
        help="Parallel worker processes (0 = auto = number of CPU cores)",
    )
    args = parser.parse_args()

    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"Error: {folder} is not a folder", file=sys.stderr)
        return 1

    out_dir = folder / args.output
    out_dir.mkdir(exist_ok=True)

    sources = collect_sources(folder)
    if not sources:
        print(f"No images found in {folder}")
        return 0

    print(f"Found {len(sources)} image(s) in {folder}")
    print(f"Writing optimized versions to {out_dir}")
    print(f"Sizes: {', '.join(f'{l}({s}px)' for l, s in SIZES)}")
    print(f"Formats: JPEG (q={JPEG_QUALITY}) + WebP (q={WEBP_QUALITY})")
    print("-" * 60)

    workers = args.jobs if args.jobs > 0 else None
    total_in = 0
    total_out = 0
    errors: list[tuple[str, str]] = []

    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process_one, p, out_dir): p for p in sources}
        for i, fut in enumerate(as_completed(futures), 1):
            src = futures[fut]
            name, outs, err = fut.result()
            if err is not None:
                errors.append((name, err))
                print(f"[{i:>3}/{len(sources)}] FAIL  {name}: {err}")
                continue
            in_size = src.stat().st_size
            out_size = sum((out_dir / o).stat().st_size for o in outs)
            total_in += in_size
            total_out += out_size
            print(
                f"[{i:>3}/{len(sources)}] OK    {name}  "
                f"{human_bytes(in_size)} -> {len(outs)} files, "
                f"{human_bytes(out_size)} total"
            )

    print("-" * 60)
    print(
        f"Done. {len(sources) - len(errors)}/{len(sources)} processed. "
        f"Source: {human_bytes(total_in)}  Output: {human_bytes(total_out)}"
    )
    if errors:
        print(f"\n{len(errors)} error(s):")
        for name, err in errors:
            print(f"  - {name}: {err}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
