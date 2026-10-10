#!/usr/bin/env python3
"""Process seller-replaced font images after the font workflow is complete.

The raw image folder is intentionally treated as immutable input. In
``--auto-order`` mode, the first stable filename in each detected ratio is
assigned ``thumbnail_main`` mechanically; all remaining files are numbered as
promos independently. No visual thumbnail identification is performed.
Exact source
copies, bounded JPEG delivery files, and a traceable manifest are written
beneath the output folder (which defaults to the raw folder itself).
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


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".tif", ".tiff"}
MAIN_RATIO = 3 / 2
SQUARE_RATIO = 1.0
RATIO_TOLERANCE = 0.025
JPEG_MAX_BYTES = 300_000


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

    lines.extend([
        "",
        "## Final handoff",
        "",
        "- Use `main/` for 3:2 marketplace delivery JPEGs.",
        "- Use `squares/` for independently supplied 1:1 marketplace delivery JPEGs.",
        "- This post-workflow processor does not package fonts, render videos, rewrite metadata, or alter the original raw images.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
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
        help="Mechanically sort direct files by filename within each ratio; first becomes thumbnail_main",
    )
    parser.add_argument("--square-japanese-thumbnail", default=None,
                        help="Optional separate raw 1:1 Japanese thumbnail filename")
    parser.add_argument("--main-promo", action="append", default=None,
                        help="Optional explicit 3:2 promo order; repeat once per raw file")
    parser.add_argument("--square-promo", action="append", default=None,
                        help="Optional explicit 1:1 promo order; repeat once per raw file")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output root; defaults to source_dir, with main/ and squares/ beneath it")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--overwrite", action="store_true",
                        help="Replace generated delivery files, never raw source files")
    parser.add_argument("--max-dim", type=int, default=None,
                        help="Downscale images so longest edge matches this pixel count")
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

    main_rows = [(main_thumbnail, "thumbnail_main.png")]
    main_rows.extend((source, f"promo_{index}.png") for index, source in enumerate(main_promos, start=1))
    square_rows = [(square_thumbnail, "thumbnail_main.png")]
    if square_japanese:
        square_rows.append((square_japanese, "thumbnail_japanese.png"))
    square_rows.extend((source, f"promo_{index}.png") for index, source in enumerate(square_promos, start=1))

    manifest_path = output_dir / "final-image-manifest.md"
    generated_paths: list[Path] = []
    for _, canonical in main_rows:
        generated_paths.extend((source_32 / canonical, main_dir / Path(canonical).with_suffix(".jpg")))
    for _, canonical in square_rows:
        generated_paths.extend((source_11 / canonical, square_dir / Path(canonical).with_suffix(".jpg")))
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

        encode_args = [sys.executable, str(Path(__file__).with_name("encode_main_jpeg.py")),
                       str(staging_32), str(main_dir), "--max-bytes", str(JPEG_MAX_BYTES)]
        if args.max_dim is not None:
            encode_args += ["--max-dim", str(args.max_dim)]
        run(encode_args, label="3:2 JPEG encoding")
        encode_args = [sys.executable, str(Path(__file__).with_name("encode_main_jpeg.py")),
                       str(staging_11), str(square_dir), "--max-bytes", str(JPEG_MAX_BYTES)]
        if args.max_dim is not None:
            encode_args += ["--max-dim", str(args.max_dim)]
        run(encode_args, label="1:1 JPEG encoding")

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
        compose_log=None,
    )
    if not manifest_path.is_file():
        fail(f"Expected generated manifest is missing: {manifest_path}")
    print(f"Final image processing complete: {output_dir}")
    print(f"Manifest: {output_dir / 'final-image-manifest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
