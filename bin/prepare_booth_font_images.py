#!/usr/bin/env python3
"""Create BOOTH-ready font image deliveries from an already named font folder.

Raw files are preserved. Every discovered image gets a compressed original-ratio
JPEG and a square JPEG. The square version uses centered white padding on the
shorter axis; a landscape 3:2 image therefore receives equal top/bottom
padding. ImageMagick performs the padding and encoding, and every delivery is
bounded to 200,000 bytes.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".tif", ".tiff"}
MAX_BYTES = 200_000


def fail(message: str) -> None:
    raise SystemExit(message)


def magick_binary(root: Path) -> str:
    candidate = root / "bin" / "magick7"
    return str(candidate) if candidate.is_file() else (shutil.which("magick") or "")


def run_magick(binary: str, args: list[str], label: str) -> None:
    result = subprocess.run([binary, *args], text=True, capture_output=True)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        fail(f"{label} failed: {detail}")


def dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            image.load()
            return image.size
    except Exception as error:
        fail(f"Could not decode {path}: {error}")


def encode(binary: str, source: Path, destination: Path, *, square: bool) -> tuple[int, int, str]:
    width, height = dimensions(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stem = destination.with_suffix("")
    quality = 92
    scale = 1.0
    padding = "none"

    while True:
        args = [str(source)]
        if square and width != height:
            side = max(width, height)
            if width > height:
                padding = f"top/bottom {side - height}px total"
            else:
                padding = f"left/right {side - width}px total"
            args += ["-background", "white", "-gravity", "center", "-extent", f"{side}x{side}"]
        if scale != 1.0:
            args += ["-resize", f"{scale * 100:.4g}%"]
        args += ["-strip", "-colorspace", "sRGB", "-quality", str(quality), "-sampling-factor", "4:2:0", str(destination)]
        run_magick(binary, args, f"Encoding {source.name}")
        if destination.stat().st_size <= MAX_BYTES:
            return width, height, padding
        if quality > 38:
            quality -= 7
        else:
            scale *= 0.9
            quality = 82
        if scale < 0.35:
            fail(f"Could not encode {source.name} at or below {MAX_BYTES} bytes")


def discover(source: Path, output: Path) -> list[Path]:
    excluded = {output.resolve()}
    images: list[Path] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        resolved = path.resolve()
        if any(parent == excluded_path or excluded_path in parent.parents for excluded_path in excluded for parent in [resolved]):
            continue
        images.append(path)
    if not images:
        fail(f"No supported images found beneath {source}")
    return images


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("font_dir", type=Path, help="Already named font workspace containing images")
    parser.add_argument("output_dir", type=Path, help="outputs/font-preparation/{number}-{slug}")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    source = args.font_dir.resolve()
    output = args.output_dir.resolve()
    if not source.is_dir():
        fail(f"Font directory does not exist: {source}")
    binary = magick_binary(args.project_root.resolve())
    if not binary:
        fail("ImageMagick is required (bin/magick7 or magick)")

    source_out = output / "visuals" / "source"
    main_out = output / "visuals" / "main"
    square_out = output / "visuals" / "squares"
    rows: list[str] = [
        "# BOOTH Font Image Processing Manifest",
        "",
        "- Contract: original-ratio and square JPEG deliveries, each <= 200000 bytes.",
        "- Padding: centered white padding on the shorter axis; landscape 3:2 receives equal top/bottom padding.",
        "- Raw source files are preserved in `visuals/source/`.",
        "",
        "| Source | Dimensions | Main bytes | Square bytes | Square treatment |",
        "|---|---:|---:|---:|---|",
    ]
    for index, image in enumerate(discover(source, output), start=1):
        stem = f"image-{index:02d}"
        source_copy = source_out / f"{stem}{image.suffix.lower()}"
        source_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image, source_copy)
        width, height = dimensions(image)
        main_path = main_out / f"{stem}.jpg"
        square_path = square_out / f"{stem}.jpg"
        _, _, _ = encode(binary, image, main_path, square=False)
        _, _, padding = encode(binary, image, square_path, square=True)
        rows.append(f"| `{image.name}` | {width}x{height} | {main_path.stat().st_size} | {square_path.stat().st_size} | {padding} |")

    manifest = output / "visuals" / "image-processing-manifest.md"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"Processed {len(rows) - 8} images")
    print(f"Image output: {output / 'visuals'}")
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
