#!/usr/bin/env python3
"""Prepare BOOTH brush delivery images without changing the approved sources.

The input directory contains a user-approved 3:2 ``thumbnail_main.png`` and
optional sequential ``promo_N.png`` files.  The script keeps exact PNG copies,
creates bounded 3:2 JPEG delivery copies, and creates padded square JPEGs.
Square derivatives contain the complete 3:2 image; they are never cropped.
"""
from __future__ import annotations

import argparse
import re
import shutil
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


CANONICAL = re.compile(r"^(thumbnail_main|promo_([0-9]+))\.png$", re.IGNORECASE)
QUALITY_LADDER = (95, 90, 85, 80, 75, 70, 65, 60, 55, 50)
SCALE_LADDER = (1.0, 0.9, 0.8, 0.7, 0.6)


def canonical_inputs(source_dir: Path) -> list[Path]:
    paths = [
        path
        for path in source_dir.iterdir()
        if path.is_file() and CANONICAL.match(path.name)
    ]
    return sorted(
        paths,
        key=lambda path: (
            0 if path.name.casefold() == "thumbnail_main.png" else 1,
            int(CANONICAL.match(path.name).group(2) or 0),
        ),
    )


def validate_inputs(paths: list[Path]) -> list[tuple[Path, int, int]]:
    if not any(path.name.casefold() == "thumbnail_main.png" for path in paths):
        raise ValueError("Missing thumbnail_main.png")

    promo_numbers = [
        int(CANONICAL.match(path.name).group(2))
        for path in paths
        if CANONICAL.match(path.name).group(2) is not None
    ]
    if promo_numbers and promo_numbers != list(range(1, len(promo_numbers) + 1)):
        raise ValueError(
            "Supporting images must be sequential promo_1.png, promo_2.png, ..."
        )

    results: list[tuple[Path, int, int]] = []
    for path in paths:
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                width, height = image.size
        except Exception as error:  # Pillow raises several image-specific types.
            raise ValueError(f"Unreadable PNG {path}: {error}") from error
        if width < 2 or height < 2:
            raise ValueError(f"Image is too small: {path}")
        ratio = width / height
        if abs(ratio - 1.5) > 0.015:
            raise ValueError(
                f"{path.name} is {width}x{height}, not an approved 3:2 image"
            )
        results.append((path, width, height))
    return results


def fit_square(image: Image.Image, canvas_size: int) -> tuple[Image.Image, tuple[int, int, int], tuple[int, int]]:
    rgb = ImageOps.exif_transpose(image).convert("RGB")
    # Always use white padding. Sampling dark artwork corners made the
    # square derivatives inherit grey/black borders in marketplace previews.
    background = (255, 255, 255)
    fitted = ImageOps.contain(
        rgb,
        (canvas_size, canvas_size),
        method=Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (canvas_size, canvas_size), background)
    offset = (
        (canvas_size - fitted.width) // 2,
        (canvas_size - fitted.height) // 2,
    )
    canvas.paste(fitted, offset)
    return canvas, background, offset


def encode_bounded(
    image: Image.Image,
    destination: Path,
    max_bytes: int,
) -> tuple[int, int, int, float]:
    """Write the largest practical JPEG that fits the byte budget."""
    rgb = image.convert("RGB")
    attempts: list[tuple[int, int, bytes]] = []
    for scale in SCALE_LADDER:
        width = max(1, round(rgb.width * scale))
        height = max(1, round(rgb.height * scale))
        scaled = rgb if scale == 1.0 else rgb.resize((width, height), Image.Resampling.LANCZOS)
        for quality in QUALITY_LADDER:
            buffer = BytesIO()
            scaled.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
                subsampling=2,
            )
            payload = buffer.getvalue()
            attempts.append((width, quality, payload))
            if len(payload) <= max_bytes:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
                return width, height, quality, scale
    smallest_width, smallest_quality, smallest_payload = attempts[-1]
    raise ValueError(
        f"Could not encode {destination.name} below {max_bytes} bytes; "
        f"smallest attempt was {len(smallest_payload)} bytes at "
        f"{smallest_width}px / quality {smallest_quality}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="prepared_visuals directory")
    parser.add_argument("output_dir", type=Path, help="outputs/brush-preparation/{slug}")
    parser.add_argument("--canvas-size", type=int, default=1600)
    parser.add_argument("--max-bytes", type=int, default=500_000)
    args = parser.parse_args()

    source_dir = args.source_dir.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory not found: {source_dir}")
    if source_dir == output_dir:
        raise SystemExit("Source and output directories must be different")
    if args.canvas_size < 2 or args.max_bytes < 1:
        raise SystemExit("canvas size and max bytes must be positive")

    paths = canonical_inputs(source_dir)
    validated = validate_inputs(paths)

    source_output = output_dir / "visuals" / "source" / "3x2"
    main_output = output_dir / "visuals" / "main"
    square_output = output_dir / "visuals" / "squares"
    source_output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for path, source_width, source_height in validated:
        exact_copy = source_output / path.name
        shutil.copy2(path, exact_copy)
        with Image.open(path) as image:
            image.load()
            main_image = ImageOps.exif_transpose(image).convert("RGB")
            square_image, background, offset = fit_square(image, args.canvas_size)

        main_path = main_output / f"{path.stem}.jpg"
        square_path = square_output / f"{path.stem}.jpg"
        main_width, main_height, main_quality, main_scale = encode_bounded(
            main_image, main_path, args.max_bytes
        )
        square_width, square_height, square_quality, square_scale = encode_bounded(
            square_image, square_path, args.max_bytes
        )
        rows.append(
            {
                "name": path.name,
                "source": str(exact_copy),
                "source_dimensions": f"{source_width}x{source_height}",
                "source_bytes": path.stat().st_size,
                "main": str(main_path),
                "main_dimensions": f"{main_width}x{main_height}",
                "main_bytes": main_path.stat().st_size,
                "main_quality": main_quality,
                "main_scale": main_scale,
                "square": str(square_path),
                "square_dimensions": f"{square_width}x{square_height}",
                "square_bytes": square_path.stat().st_size,
                "square_quality": square_quality,
                "square_scale": square_scale,
                "background": background,
                "offset": offset,
            }
        )
        print(
            f"{path.name}: source {source_width}x{source_height}; "
            f"main {main_path.stat().st_size} bytes; "
            f"square {square_path.stat().st_size} bytes"
        )

    manifest = [
        "# BOOTH Brush Visual Preparation Manifest",
        "",
        "- Source images: user-supplied approved 3:2 PNGs",
        "- Exact source copies: `visuals/source/3x2/`",
        "- Compressed 3:2 delivery copies: `visuals/main/`",
        "- Padded square delivery copies: `visuals/squares/`",
        f"- Square canvas: {args.canvas_size}x{args.canvas_size}",
        f"- Delivery byte limit: {args.max_bytes} bytes per JPEG",
        "- Square method: complete 3:2 artwork contained without cropping, with a pure white border",
        "- Pinterest derivatives: not created by this workflow",
        "",
        "| Image | Source | Main JPEG | Square JPEG | Padding | Status |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        manifest.append(
            f"| `{row['name']}` | `{row['source_dimensions']}`, {row['source_bytes']} bytes | "
            f"`{row['main_dimensions']}`, {row['main_bytes']} bytes, q{row['main_quality']} | "
            f"`{row['square_dimensions']}`, {row['square_bytes']} bytes, q{row['square_quality']} | "
            f"offset {row['offset']} / bg `{row['background']}` | PASS |"
        )
    manifest_path = output_dir / "visual-source-manifest.md"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"Wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error
