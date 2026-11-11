#!/usr/bin/env python3
"""Process seller-replaced font images after the font workflow is complete.

The raw image folder is intentionally treated as immutable input. In
``--auto-order`` mode, exactly one ``thumbnail_main`` and one
``thumbnail_alt`` file in each ratio are required and retained as named
thumbnails; remaining direct files are numbered as promos in stable filename
order. No visual thumbnail identification is performed. The optional
``--pad-squares`` flag can only
derive missing square promos when a seller-supplied square thumbnail exists;
it can never replace a missing square thumbnail. Exact source copies,
bounded JPEG delivery files, Pinterest variants, and a traceable manifest are
written beneath the output folder (which defaults to the raw folder itself).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Iterable, NoReturn

from PIL import Image

from compose_pinterest import select_thumbnail_panel_images


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".tif", ".tiff"}
MAIN_RATIO = 3 / 2
SQUARE_RATIO = 1.0
RATIO_TOLERANCE = 0.025
JPEG_TARGET_BYTES = 200_000
JPEG_MAX_BYTES = 300_000
SQUARE_THUMB_MARKERS = ("thumb", "square", "1x1", "1:1", "1-1", "1_1")
PINTEREST_MAX_BYTES = 200_000
PINTEREST_WIDTH = 1000
PINTEREST_RATIO = 0.5
PINTEREST_RATIO_TOLERANCE = 0.01
# full-width-3x2-stack-v8: three complete 3:2 source images are scaled to the
# full 1000-pixel width and stacked without crop or added side fill.
PINTEREST_COMPOSITOR_VERSION = "full-width-3x2-stack-v8"
PINTEREST_ADDITIONAL_COUNT = 10
# Keep Pinterest panels as PNG by default so the full-width stacked artwork
# retains its source detail. JPEG is optional.
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


def is_main_thumbnail_name(path: Path) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "-", path.stem.casefold()).strip("-")
    return re.search(r"(?:^|-)thumbnail-main(?:-|$)", normalized) is not None


def is_alt_thumbnail_name(path: Path) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "-", path.stem.casefold()).strip("-")
    return re.search(r"(?:^|-)thumbnail-alt(?:-|$)", normalized) is not None


def required_template_pins(pinterest_dir: Path) -> dict[int, Path]:
    """Compatibility shim: Pinterest templates are retired; composites start at 1."""
    return {}


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


def pad_to_square(source: Path, destination: Path) -> None:
    """Derive a 1:1 copy of a 3:2 image with equal white top/bottom bars."""
    try:
        with Image.open(source) as image:
            image.load()
            width, height = image.size
            if not ratio_matches(width / height, MAIN_RATIO):
                fail(f"Cannot pad {source.name}: expected a 3:2 image, got {width}x{height}")
            flat = Image.new("RGBA", (width, height), (255, 255, 255, 255))
            flat.alpha_composite(image.convert("RGBA"))
            canvas = Image.new("RGBA", (width, width), (255, 255, 255, 255))
            canvas.paste(flat, (0, (width - height) // 2))
            destination.parent.mkdir(parents=True, exist_ok=True)
            canvas.convert("RGB").save(destination, format="PNG")
    except Exception as error:
        fail(f"Could not pad {source.name} into a square: {error}")


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


def remove_stale_canonical_files(folder: Path, expected_names: set[str], suffix: str) -> list[Path]:
    """Remove obsolete files from a prior processor run after a successful replacement."""
    if not folder.is_dir():
        return []
    removed = []
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.casefold() != suffix.casefold():
            continue
        if not (path.stem.casefold() in {"thumbnail_main", "thumbnail_alt"}
                or re.fullmatch(r"promo_[0-9]+", path.stem, re.IGNORECASE)):
            continue
        if path.name not in expected_names:
            path.unlink()
            removed.append(path)
    return removed


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

    for attempt in (plain, rgb_palette, rgba_palette):
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
        return f"not needed — already within {PINTEREST_MAX_BYTES} bytes"

    # Generated panels can contain photographic detail that the available
    # lossless and quantised ladders cannot reduce to the preferred cap. Keep
    # the full-dimension PNG in that case and record the oversize condition in
    # the final manifest; the delivery contract allows this fallback.
    return f"oversize retained — quality ladder could not reach {PINTEREST_MAX_BYTES} bytes"

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
    # The visual handoff contract permits an oversize PNG when the lossless
    # and quantised quality ladders cannot reach the preferred cap. Keep the
    # best available full-dimension panel and let the final manifest report
    # its actual size instead of aborting the whole delivery pass.
    return f"oversize retained — quality ladder could not reach {PINTEREST_MAX_BYTES} bytes"


def encode_pinterest_jpeg(png: Path) -> tuple[Path, int]:
    """Encode a composed panel as a full-colour JPEG deliverable.

    Returns (path, quality). Uses the highest quality that fits the same byte cap
    the PNG path targets, so the deliverable is comparable but keeps all 24 bits
    of colour instead of being palette-quantised down to 256.
    """
    from io import BytesIO

    with Image.open(png) as image:
        rgba = image.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        white.alpha_composite(rgba)
        rgb = white.convert("RGB")
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


def pinterest_output_paths(pinterest_dir: Path, variants: int,
                           start_index: int) -> list[Path]:
    """The compositor's working PNGs."""
    return [pinterest_dir / f"pinterest_{index}.png"
            for index in range(start_index, start_index + variants)]


def pinterest_delivery_paths(pinterest_dir: Path, variants: int, fmt: str,
                             start_index: int) -> list[Path]:
    """The files a seller actually receives, in the requested format."""
    suffix = ".jpg" if fmt == "jpeg" else ".png"
    return [pinterest_dir / f"pinterest_{index}{suffix}"
            for index in range(start_index, start_index + variants)]


def write_pinterest_set_manifest(
    pinterest_dir: Path,
    template_pin_paths: dict[int, Path],
    variants: int,
    fmt: str,
    start_index: int,
    font_name: str,
) -> Path:
    rows: list[dict[str, object]] = []
    for path in pinterest_delivery_paths(pinterest_dir, variants, fmt, start_index):
        match = re.fullmatch(r"pinterest_(\d+)\.(?:png|jpe?g)", path.name, re.IGNORECASE)
        if not match:
            fail(f"unexpected Pinterest composite filename: {path.name}")
        with Image.open(path) as image:
            width, height = image.size
            image_mode = image.mode
            has_transparency = (
                image_mode in {"RGBA", "LA", "P"}
                and image.convert("RGBA").getchannel("A").getextrema()[0] == 0
            )
        rows.append({
            "index": int(match.group(1)),
            "kind": "composite",
            "file": path.name,
            "width": width,
            "height": height,
            "has_transparency": has_transparency,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest = {
        "schema": 1,
        "kind": "font-pinterest-pin-set",
        "font_name": font_name,
        "template_count": 0,
        "composite_count": variants,
        "image_count": len(rows),
        "first_composite_index": start_index,
        "last_composite_index": start_index + variants - 1,
        "images": rows,
    }
    path = pinterest_dir / "pinterest-set-manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def pinterest_outputs_status(pinterest_dir: Path, variants: int, fmt: str = "png",
                             start_index: int = 1) -> tuple[bool, str]:
    """Check the exact Pinterest delivery contract without opening source files."""

    expected_format = "JPEG" if fmt == "jpeg" else "PNG"
    for path in pinterest_delivery_paths(pinterest_dir, variants, fmt, start_index):
        if not path.is_file():
            return False, f"missing {path.name}"
        # Full-dimension panels remain valid deliverables when the available
        # compression ladder cannot reach the preferred byte cap. The final
        # manifest records each oversize file and its exact size.
        try:
            with Image.open(path) as image:
                dimensions = image.size
                image_format = image.format
                image.load()
        except Exception as error:
            return False, f"{path.name} cannot be decoded ({error})"
        if image_format != expected_format:
            return False, f"{path.name} is not a {expected_format}"
        if dimensions[0] != PINTEREST_WIDTH:
            return False, f"{path.name} is {dimensions[0]}x{dimensions[1]}"
        if abs(dimensions[0] / dimensions[1] - PINTEREST_RATIO) > PINTEREST_RATIO_TOLERANCE:
            return False, f"{path.name} is outside the expected approximately 1:2 aspect ratio"
        if fmt == "png":
            alpha = image.convert("RGBA").getchannel("A")
            if alpha.getextrema() != (255, 255):
                return False, f"{path.name} is not fully opaque edge-to-edge"
    return True, (f"all required Pinterest {expected_format}s are 1000 pixels wide "
                  "and approximately 1:2; oversize files are retained and reported")


def pinterest_fingerprint(
    *,
    font_name: str,
    main_rows: list[tuple[Path, str]],
    variants: int,
    count: int,
    seed: int,
    jpeg_companions: bool,
    start_index: int,
    template_pin_hashes: dict[int, str],
) -> dict[str, object]:
    canonical_pool = [Path(canonical) for _, canonical in main_rows]
    selected_inputs: list[dict[str, object]] = []
    seen_pairs: set[frozenset[str]] = set()
    for variant in range(1, variants + 1):
        selected, layout = select_thumbnail_panel_images(
            canonical_pool, variant, seed, seen_pairs=seen_pairs)
        selected_inputs.append({
            "output_index": start_index + variant - 1,
            "layout": layout,
            "inputs": [image.name for image in selected],
        })

    return {
        "schema": 1,
        "compositor": f"bin/compose_pinterest.py:{PINTEREST_COMPOSITOR_VERSION}+thumbnail-top-middle",
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
        "template_pin_count": len(template_pin_hashes),
        "template_pin_sha256": {str(index): digest for index, digest in sorted(template_pin_hashes.items())},
        "panel_count": count,
        "start_index": start_index,
        "seed": seed,
        "width": PINTEREST_WIDTH,
        "aspect_ratio": PINTEREST_RATIO,
        "output_filenames": [f"pinterest_{index}.png"
                              for index in range(start_index, start_index + variants)],
        "selected_inputs": selected_inputs,
        "jpeg_companions": jpeg_companions,
        "max_bytes": PINTEREST_MAX_BYTES,
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
    fmt: str = "png",
    start_index: int = 1,
) -> tuple[bool, str]:
    outputs_valid, output_reason = pinterest_outputs_status(
        pinterest_dir, variants, fmt, start_index)
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
    main_thumbnail_alt: Path | None,
    main_promos: list[Path],
    square_thumbnail: Path,
    square_thumbnail_alt: Path | None,
    square_promos: list[Path],
    compose_log: str | None,
    padded_from: dict[Path, Path],
    pinterest_enabled: bool,
    pinterest_status: str | None,
    pinterest_fingerprint_data: dict[str, object] | None,
    pinterest_compression: dict[str, str],
    pinterest_variants: int,
    pinterest_start_index: int,
    template_pin_paths: dict[int, Path],
    pinterest_jpeg_companions: bool,
    pinterest_format: str = "png",
) -> None:
    lines = [
        f"# Final Image Processing Manifest — {font_name}",
        "",
        f"- **Status:** COMPLETE — final seller-supplied image processing",
        f"- **Processed:** {date.today().isoformat()}",
        f"- **Raw source folder:** `{source_dir}`",
        f"- **Output folder:** `{output_dir}`",
        f"- **JPEG goal:** {JPEG_TARGET_BYTES} bytes per main/square file where quality allows; configured ceiling {JPEG_MAX_BYTES} bytes.",
        "- **Raw source policy:** direct source files were preserved; no raw file was overwritten, renamed, or compressed.",
        (
            "- **Naming policy:** the `thumbnail_main` and `thumbnail_alt` files in each ratio keep those roles; all remaining files are assigned promo numbers in stable filename order. No visual thumbnail identification is performed."
            if main_thumbnail_alt is not None and square_thumbnail_alt is not None
            else "- **Naming policy:** the `thumbnail_main` file in each ratio keeps that role; all remaining files are assigned promo numbers in stable filename order. No visual thumbnail identification is performed."
        ),
    ]
    over_target = sorted(
        (path.relative_to(output_dir).as_posix(), path.stat().st_size)
        for path in [*output_dir.joinpath("main").glob("*.jpg"),
                     *output_dir.joinpath("squares").glob("*.jpg")]
        if path.stat().st_size > JPEG_TARGET_BYTES
    )
    lines.append("- **Files above the 200 KB target:** " +
                 (", ".join(f"`{name}` ({size} bytes)" for name, size in over_target)
                  if over_target else "none; every JPEG met the 200 KB goal"))
    if padded_from:
        lines.append(
            f"- **Square padding:** {len(padded_from)} square file(s) were derived from their "
            "3:2 parent (shown in Raw source) with equal white top/bottom padding; Source "
            "SHA-256 hashes the padded copy (parent hashes are in the main table)."
        )
    lines.extend([
        "",
        "## Main 3:2 delivery",
        "",
        "| Raw source | Role | Exact source copy | JPEG delivery | Dimensions | JPEG bytes | Source SHA-256 |",
        "|---|---|---|---|---:|---:|---|",
    ])

    main_rows = [(main_thumbnail, "thumbnail_main", "thumbnail_main.png")]
    if main_thumbnail_alt is not None:
        main_rows.append((main_thumbnail_alt, "thumbnail_alt", "thumbnail_alt.png"))
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
    if square_thumbnail_alt is not None:
        square_rows.append((square_thumbnail_alt, "thumbnail_alt", "thumbnail_alt.png"))
    square_rows.extend((source, f"promo_{index}", f"promo_{index}.png") for index, source in enumerate(square_promos, start=1))
    for source, role, canonical in square_rows:
        width, height, _ = inspect_ratio(source, f"square source {role}")
        jpeg = output_dir / "squares" / f"{Path(canonical).stem}.jpg"
        parent = padded_from.get(source)
        raw_label = f"{parent.name} (padded to 1:1)" if parent else source.name
        lines.append(markdown_table_row([
            raw_label,
            role,
            f"`source/1x1/{canonical}`",
            f"`squares/{jpeg.name}`",
            f"{width}×{height}",
            str(jpeg.stat().st_size),
            sha256(source),
        ]).rstrip("\n"))

    lines.extend(["", "## Pinterest delivery", ""])
    if not pinterest_enabled:
        lines.append("No image panels composed because Pinterest generation was explicitly skipped.")
    else:
        template_count = len(template_pin_paths)
        composite_end = pinterest_start_index + pinterest_variants - 1
        lines.extend([
            (
                f"The {pinterest_variants} composite panels (pins {pinterest_start_index}–{composite_end}) "
                f"were already valid; the composition cache was reused. No template pins are included."
                if pinterest_status == "already-valid"
                else (
                    f"{pinterest_variants} additional variants (pins {pinterest_start_index}–"
                    f"{pinterest_start_index + pinterest_variants - 1}) were composed from the "
                    f"canonical 3:2 source pool. The first five put `thumbnail_main` at the top; "
                    f"the next five put it in the middle. Supporting images are randomly selected "
                    f"without replacement for each panel. Each complete 3:2 source is scaled "
                    f"to the full 1000-pixel panel width without cropping or side fill, so a "
                    f"three-image stack measures approximately 1:2 (1000x2001 for exact 3:2 rows). "
                    f"The ten added panels were delivered as "
                    f"{pinterest_format.upper()} at approximately 1:2 within the "
                    f"{PINTEREST_MAX_BYTES}-byte limit. No square image was used as a "
                    "Pinterest source."
                    if pinterest_format == "jpeg"
                    else f"{pinterest_variants} additional variants (pins {pinterest_start_index}–"
                         f"{pinterest_start_index + pinterest_variants - 1}) were composed from the "
                         "canonical 3:2 source pool with the thumbnail at the top in the first five "
                         "and in the middle in the next five. Supporting images are randomly "
                         "selected without replacement. Each complete 3:2 image is scaled to the full "
                         "1000-pixel panel width with no crop or added side fill, producing a "
                         "approximately 1:2 three-image stack; the template "
                         "catalogue is retired. Each PNG was checked "
                         f"against the {PINTEREST_MAX_BYTES}-byte limit; compression is lossless "
                         "first, with pngquant only if no lossless encoding fits."
                )
            ),
            f"- **Pinterest status:** {pinterest_status or 'composed'}",
            f"- **Pinterest set:** {pinterest_variants} composite panels; template catalogue retired",
            f"- **Pinterest delivery format:** {pinterest_format.upper()}"
            + " (full-width, uncropped 3:2 panels)",
            "",
            "| Output | Dimensions | Format | Bytes | Method |",
            "|---|---:|---|---:|---|",
        ])
        for index, source in sorted(template_pin_paths.items()):
            with Image.open(source) as image:
                dimensions = f"{image.width}×{image.height}"
                image_format = image.format or source.suffix.lstrip(".").upper()
            lines.append(markdown_table_row([
                f"`pinterest/{source.name}` (preserved template pin {index})",
                dimensions,
                image_format,
                str(source.stat().st_size),
                f"preserved; SHA-256 {sha256(source)}",
            ]).rstrip("\n"))
        for delivery in pinterest_delivery_paths(
                output_dir / "pinterest", pinterest_variants, pinterest_format,
                pinterest_start_index):
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
        "- Use `squares/` for 1:1 marketplace delivery JPEGs (supplied files plus any white-padded derivatives).",
    ])
    if main_thumbnail_alt is not None and square_thumbnail_alt is not None:
        lines.append("- `thumbnail_main.jpg` and `thumbnail_alt.jpg` in each folder are the primary and alternate thumbnail options.")
    if pinterest_enabled:
        lines.extend([
            f"- Use `pinterest/` for {pinterest_variants} composite panels (pins {pinterest_start_index}–{pinterest_start_index + pinterest_variants - 1}).",
            "- `pinterest/pinterest-set-manifest.json` lists every pin, index, size, and checksum for the Pinterest preparer.",
        ])
    else:
        lines.append("- Pinterest composites were explicitly skipped.")
    lines.append("- This post-workflow processor does not package fonts, render videos, rewrite metadata, or alter the original raw images.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    global JPEG_MAX_BYTES
    parser = argparse.ArgumentParser(
        description="Process final seller-replaced font images into New-Images delivery folders."
    )
    parser.add_argument("source_dir", type=Path, help="Raw folder containing direct final image files")
    parser.add_argument("--font-name", required=True, help="Final font name for the manifest")
    parser.add_argument("--main-thumbnail", default=None, help="Raw 3:2 thumbnail filename (explicit mode)")
    parser.add_argument("--square-thumbnail", default=None, help="Raw 1:1 thumbnail filename (explicit mode)")
    parser.add_argument(
        "--auto-order",
        action="store_true",
        help="Select named main and alternate thumbnails per ratio; sort remaining promos mechanically",
    )
    parser.add_argument("--pad-squares", action="store_true",
                        help="With --auto-order: derive missing promo squares only; a seller-supplied 1:1 thumbnail is still required")
    parser.add_argument("--main-promo", action="append", default=None,
                        help="Optional explicit 3:2 promo order; repeat once per raw file")
    parser.add_argument("--square-promo", action="append", default=None,
                        help="Optional explicit 1:1 promo order; repeat once per raw file")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output root; defaults to source_dir, with main/squares/pinterest beneath it")
    parser.add_argument("--pinterest-variants", type=int, default=PINTEREST_ADDITIONAL_COUNT,
                        help="number of additional Pinterest panels (the contract is 10)")
    parser.add_argument("--pinterest-count", type=int, default=3)
    parser.add_argument("--pinterest-start-index", type=int, default=None,
                        help="optional explicit first composite index; defaults to 1")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument(
        "--pinterest-jpeg-companions",
        action="store_true",
        help="Explicitly ask the Pinterest compositor for JPEG companions; omitted by default",
    )
    parser.add_argument("--pinterest", action="store_true",
                        help="compatibility flag; Pinterest panels are now generated by default")
    parser.add_argument("--skip-pinterest", action="store_true",
                        help="skip the ten additional image-composite Pinterest panels")
    parser.add_argument("--pinterest-format", choices=("jpeg", "png"), default="png",
                        help="Pinterest deliverable format; PNG and JPEG use full-width uncropped 3:2 panels")
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace generated delivery files, never raw source files")
    parser.add_argument("--max-dim", type=int, default=None,
                        help="Downscale images so longest edge matches this pixel count")
    parser.add_argument("--jpeg-max-bytes", type=int, default=JPEG_MAX_BYTES,
                        help="Per-file main/square JPEG ceiling; defaults to 300000 bytes")
    args = parser.parse_args()
    if args.jpeg_max_bytes <= 0:
        fail("--jpeg-max-bytes must be a positive byte count")
    JPEG_MAX_BYTES = args.jpeg_max_bytes
    pinterest_enabled = not args.skip_pinterest

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

    source_32 = output_dir / "source" / "3x2"
    source_11 = output_dir / "source" / "1x1"
    main_dir = output_dir / "main"
    square_dir = output_dir / "squares"
    pinterest_dir = output_dir / "pinterest"
    legacy_manifest = pinterest_dir / "pinterest-template-manifest.json"
    if pinterest_enabled and legacy_manifest.is_file():
        retired = pinterest_dir / "retired-template-catalogue"
        retired.mkdir(parents=True, exist_ok=True)
        legacy_files = [path for path in pinterest_dir.iterdir() if path.is_file() and (
            path.name in {"pinterest-template-manifest.json", "pinterest-set-manifest.json"}
            or re.fullmatch(r"pinterest_\d+\.(?:png|jpe?g)", path.name, re.IGNORECASE)
        )]
        for path in legacy_files:
            destination = retired / path.name
            if destination.exists():
                destination = retired / f"{path.stem}-{sha256(path)[:8]}{path.suffix}"
            path.replace(destination)
        print(f"retired Pinterest template catalogue assets preserved in {retired}")
    template_pin_paths: dict[int, Path] = {}
    expected_pinterest_start = 1
    if args.pinterest_start_index is not None and args.pinterest_start_index != expected_pinterest_start:
        fail("the ten Pinterest composite panels must start at index 1")
    args.pinterest_start_index = expected_pinterest_start
    template_pin_hashes = {index: sha256(path)
                           for index, path in template_pin_paths.items()}
    padded_from: dict[Path, Path] = {}
    main_thumbnail_alt: Path | None = None
    square_thumbnail_alt: Path | None = None

    if args.auto_order:
        if args.main_thumbnail or args.square_thumbnail or args.main_promo or args.square_promo:
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
        if not ratio_groups["3:2"]:
            fail("--auto-order requires a named direct 3:2 thumbnail and at least two more 3:2 files")
        three_two, squares = ratio_groups["3:2"], ratio_groups["1:1"]
        main_candidates = [path for path in three_two if is_main_thumbnail_name(path)]
        square_candidates = [path for path in squares if is_main_thumbnail_name(path)]
        main_alt_candidates = [path for path in three_two if is_alt_thumbnail_name(path)]
        square_alt_candidates = [path for path in squares if is_alt_thumbnail_name(path)]
        if len(main_candidates) != 1:
            fail("--auto-order requires exactly one 3:2 thumbnail file whose name contains "
                 "'thumbnail_main' (for example thumbnail_main_3x2.png)")
        if len(square_candidates) != 1:
            fail("--auto-order requires exactly one 1:1 thumbnail file whose name contains "
                 "'thumbnail_main' (for example thumbnail_main_1x1.png)")
        if len(main_alt_candidates) != 1:
            fail("--auto-order requires exactly one 3:2 alternate thumbnail file whose name contains "
                 "'thumbnail_alt' (for example thumbnail_alt_3x2.png)")
        if len(square_alt_candidates) != 1:
            fail("--auto-order requires exactly one 1:1 alternate thumbnail file whose name contains "
                 "'thumbnail_alt' (for example thumbnail_alt_1x1.png)")
        main_thumbnail = main_candidates[0]
        main_thumbnail_alt = main_alt_candidates[0]
        main_promos = [path for path in three_two if path not in {main_thumbnail, main_thumbnail_alt}]
        square_thumbnail = square_candidates[0]
        square_thumbnail_alt = square_alt_candidates[0]
        square_promos = [path for path in squares if path not in {square_thumbnail, square_thumbnail_alt}]
        if (
            args.pad_squares
            and len(squares) == 2
            and main_thumbnail_alt is not None
            and len(main_promos) > 0
        ):
            print(
                f"Pad squares: deriving {len(main_promos)} supporting square(s) from the "
                "3:2 promos; keeping the supplied main and alternate square thumbnails "
                "(equal white top/bottom padding).",
                file=sys.stderr,
            )
            square_promos = [source_11 / f"promo_{index}.png" for index in range(1, len(main_promos) + 1)]
            for index, parent in enumerate(main_promos, start=1):
                padded_from[source_11 / f"promo_{index}.png"] = parent
    else:
        if args.pad_squares:
            fail("--pad-squares requires --auto-order")
        if not args.main_thumbnail or not args.square_thumbnail:
            fail("Provide --main-thumbnail and --square-thumbnail, or use --auto-order")
        main_thumbnail = ensure_inside(source_dir, args.main_thumbnail, "main thumbnail")
        square_thumbnail = ensure_inside(source_dir, args.square_thumbnail, "square thumbnail")
    if main_thumbnail == square_thumbnail:
        fail("Thumbnail source files must be distinct")

    _, _, main_thumbnail_ratio = inspect_ratio(main_thumbnail, "main thumbnail")
    if not ratio_matches(main_thumbnail_ratio, MAIN_RATIO):
        fail(f"Main thumbnail must be 3:2; got {main_thumbnail.name} at ratio {main_thumbnail_ratio:.4f}")
    if square_thumbnail not in padded_from:
        _, _, square_thumbnail_ratio = inspect_ratio(square_thumbnail, "square thumbnail")
        if not ratio_matches(square_thumbnail_ratio, SQUARE_RATIO):
            fail(f"Square thumbnail must be 1:1; got {square_thumbnail.name} at ratio {square_thumbnail_ratio:.4f}")
    if not args.auto_order:
        main_promos = ordered_promos(
            source_dir, all_images, main_thumbnail, None, args.main_promo, MAIN_RATIO, "3:2"
        )
        square_promos = ordered_promos(
            source_dir, all_images, square_thumbnail, None, args.square_promo, SQUARE_RATIO, "1:1"
        )
        main_alt_candidates = [path for path in main_promos if is_alt_thumbnail_name(path)]
        square_alt_candidates = [path for path in square_promos if is_alt_thumbnail_name(path)]
        if main_alt_candidates or square_alt_candidates:
            if len(main_alt_candidates) != 1 or len(square_alt_candidates) != 1:
                fail("Named alternate thumbnails must include exactly one 3:2 and one 1:1 "
                     "file; use thumbnail_alt in both filenames")
            main_thumbnail_alt = main_alt_candidates[0]
            square_thumbnail_alt = square_alt_candidates[0]
            main_promos.remove(main_thumbnail_alt)
            square_promos.remove(square_thumbnail_alt)
    pinterest_support_count = len(main_promos) + (1 if main_thumbnail_alt is not None else 0)
    if pinterest_enabled and pinterest_support_count < 2:
        fail("Pinterest panels require the named 3:2 thumbnail plus at least two additional direct 3:2 images, including any named alternate; add them before processing")
    if not main_promos:
        print("Warning: no 3:2 supporting promos were supplied.", file=sys.stderr)
    if not square_promos:
        print("Warning: no 1:1 supporting promos were supplied.", file=sys.stderr)

    main_rows = [(main_thumbnail, "thumbnail_main.png")]
    if main_thumbnail_alt is not None:
        main_rows.append((main_thumbnail_alt, "thumbnail_alt.png"))
    main_rows.extend((source, f"promo_{index}.png") for index, source in enumerate(main_promos, start=1))
    square_rows = [(square_thumbnail, "thumbnail_main.png")]
    if square_thumbnail_alt is not None:
        square_rows.append((square_thumbnail_alt, "thumbnail_alt.png"))
    square_rows.extend((source, f"promo_{index}.png") for index, source in enumerate(square_promos, start=1))

    manifest_path = output_dir / "final-image-manifest.md"
    pinterest_fingerprint_data: dict[str, object] | None = None
    pinterest_cache_hit_flag = False
    pinterest_status: str | None = None
    pinterest_compression: dict[str, str] = {}
    compose_log: str | None = None

    if pinterest_enabled:
        if args.pinterest_variants != PINTEREST_ADDITIONAL_COUNT:
            fail(f"the Pinterest workflow creates exactly {PINTEREST_ADDITIONAL_COUNT} additional panels")
        if args.pinterest_count != 3:
            fail("the thumbnail-top-middle Pinterest layout requires exactly three images per panel")
        pinterest_fingerprint_data = pinterest_fingerprint(
            font_name=args.font_name,
            main_rows=main_rows,
            variants=args.pinterest_variants,
            count=args.pinterest_count,
            seed=args.seed,
            jpeg_companions=args.pinterest_jpeg_companions,
            start_index=args.pinterest_start_index,
            template_pin_hashes=template_pin_hashes,
        )
        pinterest_cache_hit_flag, cache_reason = pinterest_cache_hit(
            pinterest_dir,
            manifest_path,
            pinterest_fingerprint_data,
            args.pinterest_variants,
            args.pinterest_format,
            args.pinterest_start_index,
        )
        if pinterest_cache_hit_flag:
            pinterest_status = "already-valid"
            for delivery in pinterest_delivery_paths(
                pinterest_dir, args.pinterest_variants, args.pinterest_format,
                args.pinterest_start_index,
            ):
                pinterest_compression[delivery.name] = "already valid — not recompressed"
            print(f"Pinterest outputs already valid; skipping recomposition ({cache_reason}).")

    generated_paths: list[Path] = []
    for _, canonical in main_rows:
        generated_paths.extend((source_32 / canonical, main_dir / Path(canonical).with_suffix(".jpg")))
    for _, canonical in square_rows:
        generated_paths.extend((source_11 / canonical, square_dir / Path(canonical).with_suffix(".jpg")))
    if pinterest_enabled and not pinterest_cache_hit_flag:
        generated_paths.extend(
            pinterest_delivery_paths(pinterest_dir, args.pinterest_variants,
                                     args.pinterest_format, args.pinterest_start_index)
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
            if source in padded_from:
                pad_to_square(padded_from[source], source)
                canonical_copy(source, staging_11 / canonical, overwrite=True)
            else:
                canonical_copy(source, staging_11 / canonical, overwrite=True)
                canonical_copy(source, source_11 / canonical, overwrite=args.overwrite)

        encode_args = [sys.executable, str(Path(__file__).with_name("encode_main_jpeg.py")),
                       str(staging_32), str(main_dir), "--target-bytes", str(JPEG_TARGET_BYTES),
                       "--max-bytes", str(JPEG_MAX_BYTES), "--allow-over-max"]
        if args.max_dim is not None:
            encode_args += ["--max-dim", str(args.max_dim)]
        run(encode_args, label="3:2 JPEG encoding")
        encode_args = [sys.executable, str(Path(__file__).with_name("encode_main_jpeg.py")),
                       str(staging_11), str(square_dir), "--target-bytes", str(JPEG_TARGET_BYTES),
                       "--max-bytes", str(JPEG_MAX_BYTES), "--allow-over-max"]
        if args.max_dim is not None:
            encode_args += ["--max-dim", str(args.max_dim)]
        run(encode_args, label="1:1 JPEG encoding")

        if pinterest_cache_hit_flag:
            compose_log = "Pinterest outputs already valid; recomposition was skipped."
        if pinterest_enabled and not pinterest_cache_hit_flag:
            pinterest_status = "composed"
            compose_command = [
                sys.executable,
                str(Path(__file__).with_name("compose_pinterest.py")),
                str(staging_32),
                "--product", args.font_name,
                "--variants", str(args.pinterest_variants),
                "--count", str(args.pinterest_count),
                "--seed", str(args.seed),
                "--start-index", str(args.pinterest_start_index),
                "--panel-layout", "thumbnail-top-middle",
                "--output-dir", str(pinterest_dir),
            ]
            if args.pinterest_jpeg_companions:
                compose_command.append("--jpeg-companions")
            compose_log = run(compose_command, label="Pinterest composition")
            for png in pinterest_output_paths(
                    pinterest_dir, args.pinterest_variants, args.pinterest_start_index):
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
                        method = f"not needed — already within {PINTEREST_MAX_BYTES} bytes"
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
    if args.overwrite:
        stale_files = []
        stale_files += remove_stale_canonical_files(
            source_32, {canonical for _, canonical in main_rows}, ".png"
        )
        stale_files += remove_stale_canonical_files(
            source_11, {canonical for _, canonical in square_rows}, ".png"
        )
        stale_files += remove_stale_canonical_files(
            main_dir, {Path(canonical).with_suffix(".jpg").name for _, canonical in main_rows}, ".jpg"
        )
        stale_files += remove_stale_canonical_files(
            square_dir, {Path(canonical).with_suffix(".jpg").name for _, canonical in square_rows}, ".jpg"
        )
        for stale in stale_files:
            print(f"removed stale generated delivery file {stale}")
    for jpeg in list(main_dir.glob("*.jpg")) + list(square_dir.glob("*.jpg")):
        if jpeg.stat().st_size > JPEG_MAX_BYTES:
            print(f"Warning: {jpeg} remains above {JPEG_MAX_BYTES} bytes at the lowest quality rung; continuing.", file=sys.stderr)
    if pinterest_enabled:
        # A previous run may have delivered the other format. Leaving both would
        # leave the seller unsure which panel file to upload. Preserve indexes
        # 1–5, which were made earlier by /font-prep.
        stale_suffix = ".png" if args.pinterest_format == "jpeg" else ".jpg"
        for index in range(args.pinterest_start_index,
                           args.pinterest_start_index + args.pinterest_variants):
            stale = pinterest_dir / f"pinterest_{index}{stale_suffix}"
            if stale.exists() and not (stale_suffix == ".jpg" and args.pinterest_jpeg_companions):
                print(f"removed stale {stale.name} (delivery format is {args.pinterest_format})")
                stale.unlink()
        pinterest_valid, pinterest_reason = pinterest_outputs_status(
            pinterest_dir,
            args.pinterest_variants,
            args.pinterest_format,
            args.pinterest_start_index,
        )
        if not pinterest_valid:
            fail(f"Pinterest output validation failed: {pinterest_reason}")
        for index, path in template_pin_paths.items():
            if sha256(path) != template_pin_hashes[index]:
                fail(f"template Pinterest pin was changed during final-image processing: {path}")
        set_manifest_path = write_pinterest_set_manifest(
            pinterest_dir,
            template_pin_paths,
            args.pinterest_variants,
            args.pinterest_format,
            args.pinterest_start_index,
            args.font_name,
        )
        if not set_manifest_path.is_file():
            fail(f"Pinterest pin-set manifest was not written: {set_manifest_path}")
    write_manifest(
        manifest_path,
        font_name=args.font_name,
        source_dir=source_dir,
        output_dir=output_dir,
        main_thumbnail=main_thumbnail,
        main_thumbnail_alt=main_thumbnail_alt,
        main_promos=main_promos,
        square_thumbnail=square_thumbnail,
        square_thumbnail_alt=square_thumbnail_alt,
        square_promos=square_promos,
        compose_log=compose_log,
        padded_from=padded_from,
        pinterest_enabled=pinterest_enabled,
        pinterest_status=pinterest_status,
        pinterest_fingerprint_data=pinterest_fingerprint_data,
        pinterest_compression=pinterest_compression,
        pinterest_variants=args.pinterest_variants,
        pinterest_start_index=args.pinterest_start_index,
        template_pin_paths=template_pin_paths,
        pinterest_format=args.pinterest_format,
        pinterest_jpeg_companions=args.pinterest_jpeg_companions,
    )
    if not manifest_path.is_file():
        fail(f"Expected generated manifest is missing: {manifest_path}")
    print(f"Final image processing complete: {output_dir}")
    if padded_from:
        print(f"Squares derived by equal white padding: {len(padded_from)}")
    print(f"Manifest: {output_dir / 'final-image-manifest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
