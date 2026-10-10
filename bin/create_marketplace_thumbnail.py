#!/usr/bin/env python3
"""Create one crop-safe thumbnail shared by Behance and Cubebrush."""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageOps


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--canvas-width", type=int, default=1600)
    parser.add_argument("--canvas-height", type=int, default=1250)
    # The source is normally 3:2.  A 1400x933 artwork area on this mildly
    # landscape canvas leaves about 100px at the sides and 158px above/below:
    # enough crop protection without making the artwork look undersized.
    parser.add_argument("--safe-width", type=int, default=1400)
    parser.add_argument("--safe-height", type=int, default=933)
    args = parser.parse_args()

    if not args.source.is_file():
        raise SystemExit(f"Source image not found: {args.source}")
    if args.safe_width > args.canvas_width or args.safe_height > args.canvas_height:
        raise SystemExit("Safe box cannot exceed the canvas")

    with Image.open(args.source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        fitted = ImageOps.contain(image, (args.safe_width, args.safe_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (args.canvas_width, args.canvas_height), "white")
        canvas.paste(
            fitted,
            ((args.canvas_width - fitted.width) // 2, (args.canvas_height - fitted.height) // 2),
        )
        args.destination.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(args.destination, format="PNG", optimize=True, compress_level=9)
    print(
        f"{args.destination}: {args.canvas_width}x{args.canvas_height}; "
        f"artwork safe box <= {args.safe_width}x{args.safe_height}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
