#!/usr/bin/env python3
"""Process seller-replaced font images after the font workflow is complete.

The raw image folder is intentionally treated as immutable input. In
``--auto-order`` mode, the first stable filename in each detected ratio is
assigned ``thumbnail_main`` mechanically; all remaining files are numbered as
promos independently. No visual thumbnail identification is performed.
Exact source
copies, bounded JPEG delivery files, Pinterest variants, and a traceable
manifest are written beneath the output folder (which defaults to the raw
folder itself).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Iterable, NoReturn

from PIL import Image

from compose_pinterest import select_variant_images


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".tif", ".tiff"}
MAIN_RATIO = 3 / 2
SQUARE_RATIO = 1.0
RATIO_TOLERANCE = 0.025
JPEG_MAX_BYTES = 200_000
PINTEREST_MAX_BYTES = 700_000
PINTEREST_WIDTH = 1000
PINTEREST_HEIGHT = 1500
PINTEREST_COMPOSITOR_VERSION = "pillow-cache-v1"
# Pinterest panels are photo composites. A full-colour JPEG at q95 is ~half the
# size of the palette-quantised PNG the PNG cap forces, and looks far better, so
# JPEG is the default deliverable and PNG stays available for flat art.
PINTEREST_JPEG_QUALITIES = (95, 92, 90, 85, 80, 75, 70, 65, 60)
PINTEREST_PNGQUANT_SPEED = 10
PINTEREST_QUALITY_LADDERS = ("60-95", "40-85", "20-70")
PINTEREST_FINGERPRINT_START = "<!-- pinterest-fingerprint"
PINTEREST_FINGERPRINT_END = "pinterest-fingerprint -->"


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def run(command: list[str], *, label: str) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        fail(f"{label} failed ({result.returncode}): {detail}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_inside(source_dir: Path, value: str, label: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = source_dir / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(source_dir)
    except ValueError:
        fail(f"{label} must be inside the raw source folder: {value}")
    if candidate.parent != source_dir:
        fail(f"{label} must be a direct file in the raw source folder: {value}")
    if not candidate.is_file():
        fail(f"Missing {label}: {candidate}")
    if candidate.suffix.lower() not in IMAGE_SUFFIXES:
        fail(f"Unsupported image extension for {label}: {candidate.name}")
    return candidate


def direct_images(source_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def inspect_ratio(path: Path, label: str) -> tuple[int, int, float]:
    try:
        with Image.open(path) as image:
            width, height = image.size
            image.load()
    except Exception as error:  # Pillow exposes several decoder exceptions.
        fail(f"Could not decode {label} {path.name}: {error}")
    if width <= 0 or height <= 0:
        fail(f"Invalid dimensions for {label}: {path.name}")
    return width, height, width / height


def ratio_matches(value: float, target: float) -> bool:
    return abs(value - target) <= RATIO_TOLERANCE


def canonical_copy(source: Path, destination: Path, *, overwrite: bool) -> None:
    if destination.exists() and not overwrite:
        fail(f"Destination already exists; rerun with --overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def check_destinations(paths: Iterable[Path], *, overwrite: bool) -> None:
    if overwrite:
        return
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        fail("Destination files already exist; rerun with --overwrite:\n" + "\n".join(existing))


def ordered_promos(
    source_dir: Path,
    all_images: list[Path],
    thumbnail: Path,
    optional_japanese: Path | None,
    explicit: list[str] | None,
    target_ratio: float,
    label: str,
) -> list[Path]:
    excluded = {thumbnail}
    if optional_japanese:
        excluded.add(optional_japanese)

    candidates: list[Path] = []
    for path in all_images:
        if path in excluded:
            continue
        _, _, ratio = inspect_ratio(path, f"{label} candidate")
        if ratio_matches(ratio, target_ratio):
            candidates.append(path)
        elif ratio_matches(ratio, MAIN_RATIO) or ratio_matches(ratio, SQUARE_RATIO):
            # The other supported ratio is processed by the other output set.
            continue
        else:
            fail(
                f"{path.name} is neither a supported {label} ratio nor a named "
                f"thumbnail; use a 3:2 or 1:1 source image"
            )

    if explicit is None:
        return candidates

    selected = [ensure_inside(source_dir, value, f"{label} promo") for value in explicit]
    if len(set(selected)) != len(selected):
        fail(f"{label} promo list contains a duplicate source file")
    if set(selected) != set(candidates):
        missing = ", ".join(path.name for path in sorted(set(candidates) - set(selected)))
        extra = ", ".join(path.name for path in sorted(set(selected) - set(candidates)))
        detail = []
        if missing:
            detail.append(f"unlisted candidates: {missing}")
        if extra:
            detail.append(f"wrong-ratio or excluded files: {extra}")
        fail(f"Explicit {label} promo order must include every candidate ({'; '.join(detail)})")
    return selected


def rgba_bytes(path: Path) -> bytes:
    """Mode-independent pixel data, so candidates in different modes compare equal."""
    with Image.open(path) as image:
        return image.convert("RGBA").tobytes()


def lossless_png_candidate(source: Path, destination: Path, cap: int) -> str | None:
    """Try lossless encodings; return a label when one fits `cap` with identical pixels.

    A PNG re-encode is always pixel-identical, so selection is driven by SIZE, and
    the palette attempt only matters when the plain re-encode is too big.

    Palette method matters: MEDIANCUT on RGB is exact when the image really uses
    <=256 colours, while FASTOCTREE on RGBA perturbs them. So try the exact method
    first and keep the RGBA one only if it happens to be exact too. Every candidate
    is verified pixel-identical, so a "lossless" label can never be wrong.
    """
    original = rgba_bytes(source)
    attempts: list[tuple[str, callable]] = []

    def plain():
        with Image.open(source) as image:
            image.load()
            image.save(destination, format="PNG", optimize=True, compress_level=9)
        return "lossless re-encode"

    def rgb_palette():
        with Image.open(source) as image:
            image.load()
            rgb = image.convert("RGBA")
            if rgb.getchannel("A").getextrema() != (255, 255):
                return None  # real transparency: an RGB palette would flatten it
            octree = rgb.convert("RGB").quantize(colors=256, method=Image.MEDIANCUT)
            octree.save(destination, format="PNG", optimize=True, compress_level=9)
        return "lossless exact palette (<=256 colours)"

    def rgba_palette():
        with Image.open(source) as image:
            image.load()
            octree = image.convert("RGBA").quantize(colors=256, method=Image.FASTOCTREE)
            octree.save(destination, format="PNG", optimize=True, compress_level=9)
        return "lossless palette (alpha preserved)"

    attempts = [plain, rgb_palette, rgba_palette]
    for attempt in attempts:
        try:
            label = attempt()
        except (ValueError, OSError):
            continue
        if label and destination.stat().st_size <= cap and rgba_bytes(destination) == original:
            return label
    return None


def compress_png(path: Path) -> str:
    """Bring a generated PNG under the Pinterest cap, lossless first.

    pngquant is LOSSY. These panels are usually flat-colour graphic art, so a
    lossless re-encode or an exact-palette conversion often fits the cap with
    full quality intact. Every candidate is verified pixel-identical before it
    is accepted, so a lossless claim can never be wrong; pngquant is the last
    resort, not the first move.
    """
    if path.stat().st_size <= PINTEREST_MAX_BYTES:
        return "not needed — already within 700000 bytes"

    with tempfile.TemporaryDirectory(prefix="font-final-png-") as temp_dir:
        temp = Path(temp_dir)

        candidate = temp / "lossless.png"
        label = lossless_png_candidate(path, candidate, PINTEREST_MAX_BYTES)
        if label is not None:
            shutil.copy2(candidate, path)
            return f"{label} — pixels verified identical"

        pngquant = shutil.which("pngquant")
        if not pngquant:
            fail("pngquant is required to compress Pinterest PNGs that exceed the lossless paths")
        for index, quality in enumerate(PINTEREST_QUALITY_LADDERS, start=1):
            quantised = temp / f"{path.stem}-{index}.png"
            result = subprocess.run(
                [pngquant, "--force", "--speed", str(PINTEREST_PNGQUANT_SPEED), f"--quality={quality}",
                 "--output", str(quantised), str(path)],
                text=True,
                capture_output=True,
            )
            if quantised.is_file() and quantised.stat().st_size <= PINTEREST_MAX_BYTES:
                # The destination is a generated delivery file, never a raw input.
                shutil.copy2(quantised, path)
                return f"pngquant quality {quality} (lossy fallback)"
            if result.returncode not in (0, 98, 99) and result.stderr:
                fail(f"pngquant failed for {path.name}: {result.stderr.strip()}")
    fail(f"Could not compress {path.name} to {PINTEREST_MAX_BYTES} bytes")


def encode_pinterest_jpeg(png: Path) -> tuple[Path, int]:
    """Encode a composed panel as a full-colour JPEG deliverable.

    Returns (path, quality). Uses the highest quality that fits the same byte cap
    the PNG path targets, so the deliverable is comparable but keeps all 24 bits
    of colour instead of being palette-quantised down to 256.
    """
    from io import BytesIO

    with Image.open(png) as image:
        rgb = image.convert("RGB")
        for quality in PINTEREST_JPEG_QUALITIES:
            buffer = BytesIO()
            rgb.save(buffer, format="JPEG", quality=quality, optimize=True,
                     progressive=True, subsampling=2)
            payload = buffer.getvalue()
            if len(payload) <= PINTEREST_MAX_BYTES:
                destination = png.with_suffix(".jpg")
                destination.write_bytes(payload)
                return destination, quality
    fail(f"could not encode {png.name} as JPEG within {PINTEREST_MAX_BYTES} bytes")


def pinterest_output_paths(pinterest_dir: Path, variants: int) -> list[Path]:
    """The compositor's working PNGs."""
    return [pinterest_dir / f"pinterest_{index}.png" for index in range(1, variants + 1)]


def pinterest_delivery_paths(pinterest_dir: Path, variants: int, fmt: str) -> list[Path]:
    """The files a seller actually receives, in the requested format."""
    suffix = ".jpg" if fmt == "jpeg" else ".png"
    return [pinterest_dir / f"pinterest_{index}{suffix}" for index in range(1, variants + 1)]


def pinterest_outputs_status(pinterest_dir: Path, variants: int, fmt: str = "jpeg") -> tuple[bool, str]:
    """Check the exact Pinterest delivery contract without opening source files."""

    expected_format = "JPEG" if fmt == "jpeg" else "PNG"
    for path in pinterest_delivery_paths(pinterest_dir, variants, fmt):
        if not path.is_file():
            return False, f"missing {path.name}"
        if path.stat().st_size > PINTEREST_MAX_BYTES:
            return False, f"{path.name} is {path.stat().st_size} bytes"
        try:
            with Image.open(path) as image:
                dimensions = image.size
                image_format = image.format
                image.load()
        except Exception as error:
            return False, f"{path.name} cannot be decoded ({error})"
        if image_format != expected_format:
            return False, f"{path.name} is not a {expected_format}"
        if dimensions != (PINTEREST_WIDTH, PINTEREST_HEIGHT):
            return False, f"{path.name} is {dimensions[0]}x{dimensions[1]}"
    return True, (f"all required Pinterest {expected_format}s are exactly "
                   f"1000x1500 and within {PINTEREST_MAX_BYTES} bytes")


def pinterest_fingerprint(
    *,
    font_name: str,
    main_rows: list[tuple[Path, str]],
    variants: int,
    count: int,
    seed: int,
    jpeg_companions: bool,
) -> dict[str, object]:
    canonical_pool = [Path(canonical) for _, canonical in main_rows]
    selected_inputs: list[dict[str, object]] = []
    seen: set[tuple[str, ...]] = set()
    for variant in range(1, variants + 1):
        selected = select_variant_images(canonical_pool, variant, count, seed, seen)
        seen.add(tuple(image.name for image in selected))
        selected_inputs.append({
            "variant": variant,
            "inputs": [image.name for image in selected],
        })

    return {
        "schema": 1,
        "compositor": f"bin/compose_pinterest.py:{PINTEREST_COMPOSITOR_VERSION}",
        "font_name": font_name,
        "mode": "normal",
        "source_pool": [
            {
                "canonical": canonical,
                "raw_name": source.name,
                "sha256": sha256(source),
            }
            for source, canonical in main_rows
        ],
        "variants": variants,
        "panel_count": count,
        "seed": seed,
        "width": PINTEREST_WIDTH,
        "height": PINTEREST_HEIGHT,
        "output_filenames": [f"pinterest_{index}.png" for index in range(1, variants + 1)],
        "selected_inputs": selected_inputs,
        "jpeg_companions": jpeg_companions,
        "pngquant": {
            "max_bytes": PINTEREST_MAX_BYTES,
            "speed": PINTEREST_PNGQUANT_SPEED,
            "quality_ladders": list(PINTEREST_QUALITY_LADDERS),
        },
    }


def read_pinterest_fingerprint(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        start = text.index(PINTEREST_FINGERPRINT_START) + len(PINTEREST_FINGERPRINT_START)
        end = text.index(PINTEREST_FINGERPRINT_END, start)
        value = json.loads(text[start:end].strip())
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def pinterest_cache_hit(
    pinterest_dir: Path,
    manifest_path: Path,
    fingerprint: dict[str, object],
    variants: int,
    fmt: str = "jpeg",
) -> tuple[bool, str]:
    outputs_valid, output_reason = pinterest_outputs_status(pinterest_dir, variants, fmt)
    if not outputs_valid:
        return False, output_reason
    recorded = read_pinterest_fingerprint(manifest_path)
    if recorded != fingerprint:
        return False, "manifest Pinterest source hashes or options changed"
    return True, output_reason


def markdown_table_row(values: list[str]) -> str:
    escaped = [value.replace("|", "\\|") for value in values]
    return "| " + " | ".join(escaped) + " |\n"


def verify_delivery(path: Path, source: Path, target_ratio: float, label: str) -> None:
    try:
        with Image.open(path) as image:
            width, height = image.size
            image.load()
    except Exception as error:
        fail(f"Could not decode generated {label} {path.name}: {error}")
    source_width, source_height, _ = inspect_ratio(source, f"{label} source")
    if (width, height) != (source_width, source_height):
        fail(
            f"Generated {label} {path.name} changed dimensions from "
            f"{source_width}x{source_height} to {width}x{height}"
        )
    if not ratio_matches(width / height, target_ratio):
        fail(f"Generated {label} has the wrong ratio: {path}")


def write_manifest(
    path: Path,
    *,
    font_name: str,
    source_dir: Path,
    output_dir: Path,
    main_thumbnail: Path,
    main_promos: list[Path],
    square_thumbnail: Path,
    square_japanese: Path | None,
    square_promos: list[Path],
    compose_log: str | None,
    pinterest_enabled: bool,
    pinterest_status: str | None,
    pinterest_fingerprint_data: dict[str, object] | None,
    pinterest_compression: dict[str, str],
    pinterest_variants: int,
    pinterest_jpeg_companions: bool,
    pinterest_format: str = "jpeg",
) -> None:
    lines = [
        f"# Final Image Processing Manifest — {font_name}",
        "",
        f"- **Status:** COMPLETE — final seller-supplied image processing",
        f"- **Processed:** {date.today().isoformat()}",
        f"- **Raw source folder:** `{source_dir}`",
        f"- **Output folder:** `{output_dir}`",
        f"- **JPEG delivery limit:** {JPEG_MAX_BYTES} bytes per main/square file.",
        "- **Raw source policy:** direct source files were preserved; no raw file was overwritten, renamed, or compressed.",
        "- **Numbering policy:** files are assigned mechanically in stable filename order within each ratio; the first file is `thumbnail_main` and remaining files are numbered `promo_1` upward. No visual thumbnail identification is performed.",
        "",
        "## Main 3:2 delivery",
        "",
        "| Raw source | Role | Exact source copy | JPEG delivery | Dimensions | JPEG bytes | Source SHA-256 |",
        "|---|---|---|---|---:|---:|---|",
    ]

    main_rows = [(main_thumbnail, "thumbnail_main", "thumbnail_main.png")]
    main_rows.extend((source, f"promo_{index}", f"promo_{index}.png") for index, source in enumerate(main_promos, start=1))
    for source, role, canonical in main_rows:
        width, height, _ = inspect_ratio(source, f"main source {role}")
        jpeg = output_dir / "main" / f"{Path(canonical).stem}.jpg"
        lines.append(markdown_table_row([
            source.name,
            role,
            f"`source/3x2/{canonical}`",
            f"`main/{jpeg.name}`",
            f"{width}×{height}",
            str(jpeg.stat().st_size),
            sha256(source),
        ]).rstrip("\n"))

    lines.extend([
        "",
        "## Square 1:1 delivery",
        "",
        "| Raw source | Role | Exact source copy | JPEG delivery | Dimensions | JPEG bytes | Source SHA-256 |",
        "|---|---|---|---|---:|---:|---|",
    ])
    square_rows = [(square_thumbnail, "thumbnail_main", "thumbnail_main.png")]
    if square_japanese:
        square_rows.append((square_japanese, "thumbnail_japanese", "thumbnail_japanese.png"))
    square_rows.extend((source, f"promo_{index}", f"promo_{index}.png") for index, source in enumerate(square_promos, start=1))
    for source, role, canonical in square_rows:
        width, height, _ = inspect_ratio(source, f"square source {role}")
        jpeg = output_dir / "squares" / f"{Path(canonical).stem}.jpg"
        lines.append(markdown_table_row([
            source.name,
            role,
            f"`source/1x1/{canonical}`",
            f"`squares/{jpeg.name}`",
            f"{width}×{height}",
            str(jpeg.stat().st_size),
            sha256(source),
        ]).rstrip("\n"))

    lines.extend(["", "## Pinterest delivery", ""])
    if not pinterest_enabled:
        lines.append("Pinterest generation was explicitly skipped.")
    else:
        lines.extend([
            (
                "Pinterest outputs were already valid; the composition cache was reused."
                if pinterest_status == "already-valid"
                else (
                    f"{pinterest_variants} variants were composed with the Pillow-only cached "
                    f"compositor from the canonical 3:2 source pool and delivered as "
                    f"{pinterest_format.upper()} at 1000x1500 within the "
                    f"{PINTEREST_MAX_BYTES}-byte limit. No square image was used as a "
                    "Pinterest source."
                    if pinterest_format == "jpeg"
                    else f"{pinterest_variants} variants were composed with the Pillow-only cached "
                         "compositor from the canonical 3:2 source pool. Each PNG was checked "
                         f"against the {PINTEREST_MAX_BYTES}-byte limit; compression is lossless "
                         "first, with pngquant only if no lossless encoding fits."
                )
            ),
            f"- **Pinterest status:** {pinterest_status or 'composed'}",
            f"- **Pinterest delivery format:** {pinterest_format.upper()}"
            + (" (full 24-bit colour; no palette quantisation)" if pinterest_format == "jpeg" else ""),
            "",
            "| Output | Dimensions | Format | Bytes | Method |",
            "|---|---:|---|---:|---|",
        ])
        for delivery in pinterest_delivery_paths(output_dir / "pinterest", pinterest_variants, pinterest_format):
            with Image.open(delivery) as image:
                dimensions = f"{image.width}×{image.height}"
                image_format = image.format or pinterest_format.upper()
            lines.append(markdown_table_row([
                f"`pinterest/{delivery.name}`",
                dimensions,
                image_format,
                str(delivery.stat().st_size),
                pinterest_compression.get(
                    delivery.name,
                    "already valid"
                    if pinterest_status == "already-valid"
                    else "not recorded",
                ),
            ]).rstrip("\n"))
        if compose_log:
            lines.extend(["", "### Reproducible compositor log", "", "```text", compose_log.rstrip(), "```"])
        if pinterest_fingerprint_data is not None:
            lines.extend([
                "",
                "### Pinterest cache fingerprint",
                "",
                PINTEREST_FINGERPRINT_START,
                json.dumps(pinterest_fingerprint_data, indent=2, sort_keys=True),
                PINTEREST_FINGERPRINT_END,
            ])

    lines.extend([
        "",
        "## Final handoff",
        "",
        "- Use `main/` for 3:2 marketplace delivery JPEGs.",
        "- Use `squares/` for independently supplied 1:1 marketplace delivery JPEGs.",
        "- Use `pinterest/` for the four 2:3 Pinterest PNGs.",
        "- This post-workflow processor does not package fonts, render videos, rewrite metadata, or alter the original raw images.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Process final seller-replaced font images into New-Images delivery folders."
    )
    parser.add_argument("source_dir", type=Path, help="Raw folder containing direct final image files")
    parser.add_argument("--font-name", required=True, help="Final font name for the manifest and Pinterest compositor")
    parser.add_argument("--main-thumbnail", default=None, help="Raw 3:2 thumbnail filename (explicit mode)")
    parser.add_argument("--square-thumbnail", default=None, help="Raw 1:1 thumbnail filename (explicit mode)")
    parser.add_argument(
        "--auto-order",
        action="store_true",
        help="Mechanically sort direct files by filename within each ratio; first becomes thumbnail_main",
    )
    parser.add_argument("--square-japanese-thumbnail", default=None,
                        help="Optional separate raw 1:1 Japanese thumbnail filename")
    parser.add_argument("--main-promo", action="append", default=None,
                        help="Optional explicit 3:2 promo order; repeat once per raw file")
    parser.add_argument("--square-promo", action="append", default=None,
                        help="Optional explicit 1:1 promo order; repeat once per raw file")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output root; defaults to source_dir, with main/squares/pinterest beneath it")
    parser.add_argument("--pinterest-variants", type=int, default=4)
    parser.add_argument("--pinterest-count", type=int, default=3)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--pinterest-jpeg-companions",
        action="store_true",
        help="Explicitly ask the Pinterest compositor for JPEG companions; omitted by default",
    )
    parser.add_argument("--skip-pinterest", action="store_true")
    parser.add_argument("--pinterest-format", choices=("jpeg", "png"), default="jpeg",
                        help="Pinterest deliverable format; JPEG keeps full colour at "
                             "roughly half the bytes of a palette-quantised PNG")
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace generated delivery files, never raw source files")
    args = parser.parse_args()

    source_dir = args.source_dir.expanduser().resolve()
    if not source_dir.is_dir():
        fail(f"Raw source folder not found: {source_dir}")
    output_dir = (args.output_dir or source_dir).expanduser().resolve()
    if output_dir == source_dir or source_dir in output_dir.parents:
        # This is the intended layout: output subfolders live beside the raw files.
        pass
    elif output_dir in source_dir.parents:
        fail("Output directory may not contain the raw source folder")

    all_images = direct_images(source_dir)
    if not all_images:
        fail(f"No direct raster images found in {source_dir}")

    if args.auto_order:
        if args.main_thumbnail or args.square_thumbnail or args.square_japanese_thumbnail or args.main_promo or args.square_promo:
            fail("--auto-order cannot be combined with explicit thumbnail or promo filenames")
        ratio_groups: dict[str, list[Path]] = {"3:2": [], "1:1": []}
        for image in all_images:
            _, _, ratio = inspect_ratio(image, f"auto-order candidate {image.name}")
            if ratio_matches(ratio, MAIN_RATIO):
                ratio_groups["3:2"].append(image)
            elif ratio_matches(ratio, SQUARE_RATIO):
                ratio_groups["1:1"].append(image)
            else:
                fail(f"{image.name} is neither 3:2 nor 1:1; auto-order cannot classify it")
        if not ratio_groups["3:2"] or not ratio_groups["1:1"]:
            fail("--auto-order requires at least one direct 3:2 file and one direct 1:1 file")
        main_thumbnail, square_thumbnail = ratio_groups["3:2"][0], ratio_groups["1:1"][0]
        square_japanese = None
        main_promos, square_promos = ratio_groups["3:2"][1:], ratio_groups["1:1"][1:]
    else:
        if not args.main_thumbnail or not args.square_thumbnail:
            fail("Provide --main-thumbnail and --square-thumbnail, or use --auto-order")
        main_thumbnail = ensure_inside(source_dir, args.main_thumbnail, "main thumbnail")
        square_thumbnail = ensure_inside(source_dir, args.square_thumbnail, "square thumbnail")
        square_japanese = (
            ensure_inside(source_dir, args.square_japanese_thumbnail, "square Japanese thumbnail")
            if args.square_japanese_thumbnail else None
        )
    if len({main_thumbnail, square_thumbnail, square_japanese} - {None}) != (2 if square_japanese is None else 3):
        fail("Thumbnail source files must be distinct")

    _, _, main_thumbnail_ratio = inspect_ratio(main_thumbnail, "main thumbnail")
    if not ratio_matches(main_thumbnail_ratio, MAIN_RATIO):
        fail(f"Main thumbnail must be 3:2; got {main_thumbnail.name} at ratio {main_thumbnail_ratio:.4f}")
    _, _, square_thumbnail_ratio = inspect_ratio(square_thumbnail, "square thumbnail")
    if not ratio_matches(square_thumbnail_ratio, SQUARE_RATIO):
        fail(f"Square thumbnail must be 1:1; got {square_thumbnail.name} at ratio {square_thumbnail_ratio:.4f}")
    if square_japanese:
        _, _, japanese_ratio = inspect_ratio(square_japanese, "square Japanese thumbnail")
        if not ratio_matches(japanese_ratio, SQUARE_RATIO):
            fail(f"Square Japanese thumbnail must be 1:1; got {square_japanese.name}")

    if not args.auto_order:
        main_promos = ordered_promos(
            source_dir, all_images, main_thumbnail, None, args.main_promo, MAIN_RATIO, "3:2"
        )
        square_promos = ordered_promos(
            source_dir, all_images, square_thumbnail, square_japanese, args.square_promo, SQUARE_RATIO, "1:1"
        )
    if not main_promos:
        print("Warning: no 3:2 supporting promos were supplied.", file=sys.stderr)
    if not square_promos:
        print("Warning: no 1:1 supporting promos were supplied.", file=sys.stderr)

    source_32 = output_dir / "source" / "3x2"
    source_11 = output_dir / "source" / "1x1"
    main_dir = output_dir / "main"
    square_dir = output_dir / "squares"
    pinterest_dir = output_dir / "pinterest"

    main_rows = [(main_thumbnail, "thumbnail_main.png")]
    main_rows.extend((source, f"promo_{index}.png") for index, source in enumerate(main_promos, start=1))
    square_rows = [(square_thumbnail, "thumbnail_main.png")]
    if square_japanese:
        square_rows.append((square_japanese, "thumbnail_japanese.png"))
    square_rows.extend((source, f"promo_{index}.png") for index, source in enumerate(square_promos, start=1))

    manifest_path = output_dir / "final-image-manifest.md"
    pinterest_fingerprint_data: dict[str, object] | None = None
    pinterest_cache_hit_flag = False
    pinterest_status: str | None = None
    pinterest_compression: dict[str, str] = {}

    if not args.skip_pinterest:
        if args.pinterest_variants < 1:
            fail("--pinterest-variants must be at least 1")
        if args.pinterest_count < 1:
            fail("--pinterest-count must be at least 1")
        pinterest_fingerprint_data = pinterest_fingerprint(
            font_name=args.font_name,
            main_rows=main_rows,
            variants=args.pinterest_variants,
            count=args.pinterest_count,
            seed=args.seed,
            jpeg_companions=args.pinterest_jpeg_companions,
        )
        pinterest_cache_hit_flag, cache_reason = pinterest_cache_hit(
            pinterest_dir,
            manifest_path,
            pinterest_fingerprint_data,
            args.pinterest_variants,
            args.pinterest_format,
        )
        if pinterest_cache_hit_flag:
            pinterest_status = "already-valid"
            for delivery in pinterest_delivery_paths(
                pinterest_dir, args.pinterest_variants, args.pinterest_format
            ):
                pinterest_compression[delivery.name] = "already valid — not recompressed"
            print(f"Pinterest outputs already valid; skipping recomposition and pngquant ({cache_reason}).")

    generated_paths: list[Path] = []
    for _, canonical in main_rows:
        generated_paths.extend((source_32 / canonical, main_dir / Path(canonical).with_suffix(".jpg")))
    for _, canonical in square_rows:
        generated_paths.extend((source_11 / canonical, square_dir / Path(canonical).with_suffix(".jpg")))
    if not args.skip_pinterest and not pinterest_cache_hit_flag:
        generated_paths.extend(
            pinterest_delivery_paths(pinterest_dir, args.pinterest_variants, args.pinterest_format)
        )
    check_destinations([*generated_paths, manifest_path], overwrite=args.overwrite)

    with tempfile.TemporaryDirectory(prefix="font-final-canonical-") as temp_dir:
        staging = Path(temp_dir)
        staging_32 = staging / "3x2"
        staging_11 = staging / "1x1"
        for source, canonical in main_rows:
            canonical_copy(source, staging_32 / canonical, overwrite=True)
            canonical_copy(source, source_32 / canonical, overwrite=args.overwrite)
        for source, canonical in square_rows:
            canonical_copy(source, staging_11 / canonical, overwrite=True)
            canonical_copy(source, source_11 / canonical, overwrite=args.overwrite)

        run([sys.executable, str(Path(__file__).with_name("encode_main_jpeg.py")),
             str(staging_32), str(main_dir), "--max-bytes", str(JPEG_MAX_BYTES)],
            label="3:2 JPEG encoding")
        run([sys.executable, str(Path(__file__).with_name("encode_main_jpeg.py")),
             str(staging_11), str(square_dir), "--max-bytes", str(JPEG_MAX_BYTES)],
            label="1:1 JPEG encoding")

        compose_log: str | None = None
        if pinterest_cache_hit_flag:
            compose_log = "Pinterest outputs already valid; recomposition and pngquant were skipped."
        if not args.skip_pinterest and not pinterest_cache_hit_flag:
            pinterest_status = "composed"
            compose_command = [
                sys.executable,
                str(Path(__file__).with_name("compose_pinterest.py")),
                str(staging_32),
                "--product", args.font_name,
                "--variants", str(args.pinterest_variants),
                "--count", str(args.pinterest_count),
                "--seed", str(args.seed),
                "--output-dir", str(pinterest_dir),
            ]
            if args.pinterest_jpeg_companions:
                compose_command.append("--jpeg-companions")
            compose_log = run(compose_command, label="Pinterest composition")
            for png in pinterest_output_paths(pinterest_dir, args.pinterest_variants):
                if not png.is_file():
                    fail(f"Pinterest compositor did not create {png}")
                if args.pinterest_format == "jpeg":
                    jpeg, quality = encode_pinterest_jpeg(png)
                    method = f"JPEG q{quality}, full 24-bit colour"
                    pinterest_compression[jpeg.name] = method
                    pinterest_compression[png.name] = "removed — JPEG is the deliverable"
                    print(f"{png.name} ({png.stat().st_size} B) -> {jpeg.name}: "
                          f"{jpeg.stat().st_size} B ({method})")
                    png.unlink()
                else:
                    if png.stat().st_size > PINTEREST_MAX_BYTES:
                        method = compress_png(png)
                    else:
                        method = "not needed — already within 700000 bytes"
                    pinterest_compression[png.name] = method
                    print(f"{png.name}: {png.stat().st_size} bytes ({method})")

    for path in generated_paths:
        if not path.is_file():
            fail(f"Expected generated file is missing: {path}")
    for source, canonical in main_rows:
        canonical_path = source_32 / canonical
        if sha256(source) != sha256(canonical_path):
            fail(f"Source copy is not byte-identical: {canonical_path}")
        verify_delivery(main_dir / Path(canonical).with_suffix(".jpg"), source, MAIN_RATIO, "3:2 JPEG")
    for source, canonical in square_rows:
        canonical_path = source_11 / canonical
        if sha256(source) != sha256(canonical_path):
            fail(f"Source copy is not byte-identical: {canonical_path}")
        verify_delivery(square_dir / Path(canonical).with_suffix(".jpg"), source, SQUARE_RATIO, "1:1 JPEG")
    for jpeg in list(main_dir.glob("*.jpg")) + list(square_dir.glob("*.jpg")):
        if jpeg.stat().st_size > JPEG_MAX_BYTES:
            fail(f"JPEG exceeds {JPEG_MAX_BYTES} bytes: {jpeg}")
    if not args.skip_pinterest:
        # A previous run may have delivered the other format. Leaving both would
        # leave the seller unsure which file to upload, so drop the other one
        # whether this run composed panels or reused the cache.
        stale_suffix = ".png" if args.pinterest_format == "jpeg" else ".jpg"
        for stale in sorted(pinterest_dir.glob(f"pinterest_*{stale_suffix}")):
            if stale_suffix == ".jpg" and args.pinterest_jpeg_companions:
                continue
            print(f"removed stale {stale.name} (delivery format is {args.pinterest_format})")
            stale.unlink()
        pinterest_valid, pinterest_reason = pinterest_outputs_status(
            pinterest_dir,
            args.pinterest_variants,
            args.pinterest_format,
        )
        if not pinterest_valid:
            fail(f"Pinterest output validation failed: {pinterest_reason}")

    write_manifest(
        manifest_path,
        font_name=args.font_name,
        source_dir=source_dir,
        output_dir=output_dir,
        main_thumbnail=main_thumbnail,
        main_promos=main_promos,
        square_thumbnail=square_thumbnail,
        square_japanese=square_japanese,
        square_promos=square_promos,
        compose_log=compose_log,
        pinterest_enabled=not args.skip_pinterest,
        pinterest_status=pinterest_status,
        pinterest_fingerprint_data=pinterest_fingerprint_data,
        pinterest_compression=pinterest_compression,
        pinterest_variants=args.pinterest_variants,
        pinterest_format=args.pinterest_format,
        pinterest_jpeg_companions=args.pinterest_jpeg_companions,
    )
    if not manifest_path.is_file():
        fail(f"Expected generated manifest is missing: {manifest_path}")
    print(f"Final image processing complete: {output_dir}")
    print(f"Manifest: {output_dir / 'final-image-manifest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
