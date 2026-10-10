#!/usr/bin/env python3
"""Stack prepared product visuals into standard 1000x1500 2:3 Pinterest PNG and JPG files."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from PIL import Image

TARGET_WIDTH = 1000
TARGET_HEIGHT = 1500

def tool(*names: str) -> str:
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    raise SystemExit(f"Missing required tool: {', '.join(names)}")

def run(command: list[str]) -> None:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(command)}\n{detail}")

def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    if not value:
        raise ValueError("Product name produces an empty slug")
    return value

def first_existing(directory: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None

def numbered_images(directory: Path, prefix: str, suffix: str = ".png") -> list[Path]:
    found: list[tuple[int, Path]] = []
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+){re.escape(suffix)}$", re.IGNORECASE)
    for path in directory.iterdir():
        match = pattern.match(path.name)
        if match and path.is_file():
            found.append((int(match.group(1)), path))
    return [path for _, path in sorted(found)]

def select_variant_images(
    pool: list[Path],
    variant: int,
    count: int,
    seed: int,
    seen: set[tuple[str, ...]],
) -> list[Path]:
    """Select images for a Pinterest variant, avoiding previously used combinations.
    
    Args:
        pool: List of available canonical images.
        variant: Variant number (1-based).
        count: Number of images to select.
        seed: Random seed for deterministic selection.
        seen: Set of previously used image combinations (as tuples of names).
    
    Returns:
        List of selected images.
    """
    import random
    
    # Create a seeded random generator for deterministic selection
    rng = random.Random(seed + variant)
    
    # Shuffle indices for this variant
    indices = list(range(len(pool)))
    rng.shuffle(indices)
    
    # Try to find a combination that hasn't been seen
    for _ in range(100):  # Limit attempts to avoid infinite loop
        selected = [pool[i] for i in indices[:count]]
        combo = tuple(img.name for img in selected)
        if combo not in seen:
            return selected
        # Shuffle again if we've seen this combination
        rng.shuffle(indices)
    
    # If we can't find a new combination, return what we have
    return [pool[i] for i in indices[:count]]

def collect_images(directory: Path, mode: str, count: int | None) -> tuple[str, list[Path]]:
    normal_main = first_existing(directory, ("thumbnail_main.png", "thumbnail.png", "main.png"))
    normal_promos = numbered_images(directory, "promo")
    square_main = first_existing(directory, ("thumbnail_square.png", "main_square.png"))
    square_promos = numbered_images(directory, "promo", "_square.png")

    if mode == "normal":
        if not normal_main:
            raise SystemExit(f"No main 3:2 thumbnail found in {directory}")
        images = [normal_main] + normal_promos
        limit = count or 3
        return "normal", images[:limit]

    if mode == "square":
        if not square_main:
            raise SystemExit(f"No main square thumbnail found in {directory}")
        images = [square_main] + square_promos
        limit = count or 3
        return "square", images[:limit]

    if normal_main:
        images = [normal_main] + normal_promos
        limit = count or (3 if len(images) >= 3 else len(images))
        return "normal", images[:limit]

    if square_main:
        images = [square_main] + square_promos
        limit = count or (3 if len(images) >= 3 else len(images))
        return "square", images[:limit]

    raise SystemExit("Could not find usable product images.")

def compose(convert: str, images: list[Path], width: int, raw_output: Path) -> None:
    """Stack images into a 2:3 panel by fitting each one whole — never cropping.

    Every image is scaled to fit inside its slot, then centred on a white
    canvas of the slot size. Landscape 3:2 sources keep their full content;
    the leftover width becomes equal white margins instead of a centre-crop
    that used to slice the top and bottom images of a 3-image stack.
    """
    target_height = round(width * 1.5)
    count = len(images)
    if count < 1:
        raise SystemExit("compose_pinterest: no images to stack")
    slot_heights = [target_height // count] * count
    for index in range(target_height % count):
        slot_heights[index] += 1
    with tempfile.TemporaryDirectory(prefix="pinterest-compose-") as temp_dir:
        panels: list[Path] = []
        for index, (image, slot_height) in enumerate(zip(images, slot_heights), start=1):
            panel = Path(temp_dir) / f"panel-{index}.png"
            run([
                convert,
                str(image),
                "-resize", f"{width}x{slot_height}",
                "-background", "white",
                "-gravity", "center",
                "-extent", f"{width}x{slot_height}",
                "+repage",
                str(panel),
            ])
            panels.append(panel)
        run([convert, *[str(panel) for panel in panels], "-append", str(raw_output)])

def process_truecolor_outputs(raw_output: Path, final_png: Path) -> tuple[Path, Path]:
    final_png.parent.mkdir(parents=True, exist_ok=True)
    final_jpg = final_png.with_suffix(".jpg")

    with Image.open(raw_output) as img:
        rgb_img = img.convert("RGB")
        rgb_img = rgb_img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
        rgb_img.save(final_png, format="PNG", optimize=True)
        rgb_img.save(final_jpg, format="JPEG", quality=95, optimize=True)

    return final_png, final_jpg

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stack prepared product images into standard 1000x1500 2:3 Pinterest PNG and JPG files."
    )
    parser.add_argument("directory", type=Path, help="Directory containing the prepared product images")
    parser.add_argument("--product", required=True, help="Product name used for the output filename")
    parser.add_argument("--mode", choices=("auto", "normal", "square"), default="auto")
    parser.add_argument("--count", type=int, default=None, help="Number of images to stack")
    parser.add_argument("--output", type=Path, default=None, help="Optional output path for PNG")
    parser.add_argument("--variants", type=int, default=1, help="Number of Pinterest variants to create")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic variant selection")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory for variant files")
    parser.add_argument("--jpeg-companions", action="store_true", help="Also create JPEG companion files")

    args = parser.parse_args()
    directory = args.directory.expanduser().resolve()
    if not directory.is_dir():
        raise SystemExit(f"Directory not found: {directory}")

    convert = tool("magick", "convert")
    selected_mode, images = collect_images(directory, args.mode, args.count)
    
    # Handle single output or multiple variants
    if args.variants == 1:
        # Never default into the input directory: that directory holds the exact
        # source images, and a composed 1000x1500 panel written there is picked up
        # as a stack input by the next run (collect_images reads this directory).
        output_png = (
            args.output
            or directory / "pinterest" / f"{slugify(args.product)}-pinterest.png"
        ).expanduser().resolve()
        if output_png.parent == directory:
            raise SystemExit(
                f"refusing to write {output_png.name} into the source directory "
                f"({directory}); pass --output or --output-dir outside it"
            )
        output_png.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="pinterest-output-") as temp_dir:
            raw_path = Path(temp_dir) / "raw.png"
            compose(convert, images, TARGET_WIDTH, raw_path)
            png_path, jpg_path = process_truecolor_outputs(raw_path, output_png)
        
        print(f"Output PNG (24-bit Truecolor RGB): {png_path} ({png_path.stat().st_size / 1024:.1f} KB)")
        print(f"Output JPG (High-Quality 95%): {jpg_path} ({jpg_path.stat().st_size / 1024:.1f} KB)")
        print(f"Mode: {selected_mode}; stacked {len(images)} images")
        print("Inputs: " + ", ".join(image.name for image in images))
        print(f"Dimensions: {TARGET_WIDTH}x{TARGET_HEIGHT} (exact 2:3 ratio)")
    else:
        # Multiple variants mode
        output_dir = (args.output_dir or directory / "pinterest").expanduser().resolve()
        if output_dir == directory:
            raise SystemExit(
                f"refusing to write Pinterest panels into the source directory "
                f"({directory}); pass --output-dir outside it"
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for variant in range(1, args.variants + 1):
            variant_images = select_variant_images(images, variant, args.count or 3, args.seed, set())
            output_png = output_dir / f"pinterest_{variant}.png"
            
            with tempfile.TemporaryDirectory(prefix="pinterest-output-") as temp_dir:
                raw_path = Path(temp_dir) / "raw.png"
                compose(convert, variant_images, TARGET_WIDTH, raw_path)
                png_path, jpg_path = process_truecolor_outputs(raw_path, output_png)
            
            print(f"Variant {variant}: {png_path.name} ({png_path.stat().st_size / 1024:.1f} KB)")
            if args.jpeg_companions:
                print(f"Variant {variant}: {jpg_path.name} ({jpg_path.stat().st_size / 1024:.1f} KB)")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
