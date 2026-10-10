#!/usr/bin/env python3
"""Re-encode prepared PNGs losslessly without changing their pixels."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageChops


CANONICAL = re.compile(r"^(thumbnail_main|promo_[0-9]+)\.png$", re.IGNORECASE)


def canonical_inputs(source_dir: Path) -> list[Path]:
    files = [path for path in source_dir.iterdir() if path.is_file() and CANONICAL.match(path.name)]
    return sorted(
        files,
        key=lambda path: (0 if path.name.casefold() == "thumbnail_main.png" else 1, path.name.casefold()),
    )


def optimize_one(source: Path, destination: Path) -> tuple[int, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() == destination.resolve():
        raise ValueError(f"Refusing to overwrite source image: {source}")

    with Image.open(source) as image:
        image.load()
        save_kwargs: dict[str, object] = {
            "format": "PNG",
            "optimize": True,
            "compress_level": 9,
        }
        # Preserve common non-pixel metadata when Pillow exposes it. The
        # pixel comparison below remains the authoritative quality guarantee.
        for key in ("icc_profile", "dpi", "exif", "transparency"):
            if key in image.info:
                save_kwargs[key] = image.info[key]
        image.save(destination, **save_kwargs)
        source_pixels = image.convert("RGBA")

    with Image.open(destination) as optimized:
        optimized.load()
        optimized_pixels = optimized.convert("RGBA")
        if source_pixels.size != optimized_pixels.size:
            raise RuntimeError(f"Dimensions changed while optimizing {source}")
        if ImageChops.difference(source_pixels, optimized_pixels).getbbox() is not None:
            raise RuntimeError(f"Pixel data changed while optimizing {source}")

    return source.stat().st_size, destination.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="Directory containing untouched canonical 3:2 PNGs")
    parser.add_argument("output_dir", type=Path, help="Separate directory for losslessly optimized PNGs")
    args = parser.parse_args()

    source_dir = args.source_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")
    if source_dir == output_dir:
        raise SystemExit("Source and output directories must be different")

    inputs = canonical_inputs(source_dir)
    if not inputs:
        raise SystemExit(f"No thumbnail_main.png or promo_N.png files found in {source_dir}")

    for source in inputs:
        destination = output_dir / source.name
        before, after = optimize_one(source, destination)
        print(f"{source.name}: {before} -> {after} bytes; pixel-identical")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
