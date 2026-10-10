#!/usr/bin/env python3
"""Render Agent-27's authored font artwork into a prepared handoff.

This is deliberately a mechanical step. It does not select a composition,
apply a template, typeset copy, recolor artwork, or invent a replacement image.
OpenPencil .fig files are the primary source for new handoffs. The legacy
outlined-SVG path remains available for older handoffs only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import unquote


RATIOS = (("3x2", 2400, 1600), ("1x1", 1600, 1600))
PROMO_RE = re.compile(r"^promo_(\d+)\.svg$")


def resolve_path(value: str, plan_path: Path) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate
    return (plan_path.parent / candidate).resolve()


def source_for(asset: dict[str, Any], ratio: str, artwork_root: Path, name: str) -> Path:
    source_files = asset.get("source_files")
    if isinstance(source_files, dict) and isinstance(source_files.get(ratio), str):
        return (artwork_root.parent / source_files[ratio]).resolve()
    return artwork_root / ratio / f"{name}.svg"


def require_text(plan: dict[str, Any], key: str) -> str:
    value = plan.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"visual plan requires a non-empty {key}")
    return value


def validate_source(
    path: Path,
    allow_raster_assets: bool = False,
    approved_raster_paths: set[Path] | None = None,
    approved_embedded_assets: set[str] | None = None,
) -> None:
    if not path.is_file():
        raise SystemExit(f"missing custom artwork source: {path}")
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except (OSError, ET.ParseError) as error:
        raise SystemExit(f"unreadable SVG source {path}: {error}") from error
    tag = root.tag.rsplit("}", 1)[-1]
    if tag != "svg":
        raise SystemExit(f"custom artwork is not an SVG document: {path}")
    forbidden = {"text", "foreignObject"}
    if any(element.tag.rsplit("}", 1)[-1] in forbidden for element in root.iter()):
        raise SystemExit(f"custom artwork must use outlined/vector lettering, not text elements: {path}")
    images = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "image"]
    if images and not allow_raster_assets:
        raise SystemExit(f"raster/image elements require explicit approved_raster_assets provenance: {path}")
    for image in images:
        href = image.attrib.get("href") or image.attrib.get("{http://www.w3.org/1999/xlink}href")
        if not href:
            raise SystemExit(f"raster artwork image has no source reference: {path}")
        if href.startswith("data:"):
            digest = hashlib.sha256(href.encode("utf-8")).hexdigest()
            if f"embedded:{digest}" not in (approved_embedded_assets or set()):
                raise SystemExit(f"embedded raster artwork is not bound to approved_raster_assets: {path}")
        else:
            resolved = (path.parent / unquote(href)).resolve()
            if resolved not in (approved_raster_paths or set()):
                raise SystemExit(f"raster artwork source is not bound to approved_raster_assets: {resolved}")
    if not any(element.tag.rsplit("}", 1)[-1] == "path" for element in root.iter()):
        raise SystemExit(f"custom artwork has no path geometry: {path}")


def render_svg(source: Path, destination: Path, width: int, height: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "rsvg-convert",
            "--width",
            str(width),
            "--height",
            str(height),
            "--output",
            str(destination),
            str(source),
        ],
        check=True,
    )


def render_specimens(plan: dict[str, Any], plan_path: Path, output: Path) -> None:
    primary = plan.get("primary_font")
    if not isinstance(primary, str) or not primary.strip():
        raise SystemExit("visual plan requires primary_font for factual specimens")
    primary_path = resolve_path(primary, plan_path)
    if not primary_path.is_file():
        raise SystemExit(f"font file not found: {primary_path}")

    temporary = output / ".specimen-render"
    if temporary.exists():
        shutil.rmtree(temporary)
    script = Path(__file__).with_name("render_font_specimens.py")
    subprocess.run(
        [sys.executable, str(script), str(primary_path), str(temporary), "--name", require_text(plan, "font_name")],
        check=True,
    )
    for ratio, source_name in (("3x2", "main"), ("1x1", "squares")):
        destination = output / "specimens" / ratio
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("specimen-alphabet-numerals.png", "specimen-multilingual-glyphs.png"):
            source = temporary / source_name / name
            if not source.is_file():
                raise SystemExit(f"specimen renderer did not create {source}")
            shutil.copy2(source, destination / name)
    shutil.rmtree(temporary)


def render_direct(plan: dict[str, Any], plan_path: Path, output: Path) -> None:
    if plan.get("render_mode") not in {"direct_artwork", "direct"}:
        raise SystemExit("custom handoff rasterizer requires render_mode=direct_artwork")
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing visual handoff: {output}")
    if not shutil.which("rsvg-convert"):
        raise SystemExit("rsvg-convert is required but was not found on PATH")

    promos = plan.get("promos")
    if not isinstance(promos, list) or not 4 <= len(promos) <= 8:
        raise SystemExit("visual plan must contain 4-8 supporting promos")
    artwork_value = plan.get("artwork_root", "artwork")
    if not isinstance(artwork_value, str) or not artwork_value.strip():
        raise SystemExit("visual plan artwork_root must be a non-empty path")
    artwork_root = resolve_path(artwork_value, plan_path)
    allow_raster_assets = plan.get("allow_raster_assets") is True
    approved_raster_paths: set[Path] = set()
    approved_embedded_assets: set[str] = set()
    if allow_raster_assets:
        approved_assets = plan.get("approved_raster_assets")
        if not isinstance(approved_assets, list) or not approved_assets:
            raise SystemExit("allow_raster_assets requires a non-empty approved_raster_assets record")
        for index, asset in enumerate(approved_assets, start=1):
            if not isinstance(asset, dict) or not isinstance(asset.get("path"), str) or not isinstance(asset.get("provenance"), str):
                raise SystemExit(f"approved_raster_assets[{index}] requires path and provenance")
            asset_path = asset["path"]
            if asset_path.startswith("embedded:"):
                approved_embedded_assets.add(asset_path)
            else:
                approved_raster_paths.add(resolve_path(asset_path, plan_path))
    assets: list[tuple[str, dict[str, Any], str]] = [("thumbnail_main", plan.get("thumbnail", {}), "thumbnail_main")]
    assets.extend((f"promo_{index}", promo, f"promo_{index}") for index, promo in enumerate(promos, start=1))
    jobs: list[tuple[str, str, int, int, Path, Path, Path]] = []
    for ratio, width, height in RATIOS:
        for asset_name, asset, filename in assets:
            if not isinstance(asset, dict):
                raise SystemExit(f"visual plan asset is not an object: {asset_name}")
            source = source_for(asset, ratio, artwork_root, filename)
            validate_source(source, allow_raster_assets, approved_raster_paths, approved_embedded_assets)
            svg_destination = output / "svg" / ratio / f"{filename}.svg"
            png_destination = output / ratio / f"{filename}.png"
            jobs.append((asset_name, ratio, width, height, source, svg_destination, png_destination))
    japanese = plan.get("japanese_thumbnail")
    if isinstance(japanese, dict):
        source = source_for(japanese, "1x1", artwork_root, "thumbnail_japanese")
        validate_source(source, allow_raster_assets, approved_raster_paths, approved_embedded_assets)
        svg_destination = output / "svg" / "1x1" / "thumbnail_japanese.svg"
        jobs.append(("thumbnail_japanese", "1x1", 1600, 1600, source, svg_destination, output / "1x1" / "thumbnail_japanese.png"))
    else:
        raise SystemExit("direct artwork requires japanese_thumbnail")

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = output.with_name(f"{output.name}.staging")
    if staging.exists():
        raise SystemExit(f"refusing to reuse existing staging directory: {staging}")
    staging.mkdir(parents=True)
    try:
        for _asset_name, _ratio, width, height, source, _svg_destination, _png_destination in jobs:
            svg_destination = staging / _svg_destination.relative_to(output)
            png_destination = staging / _png_destination.relative_to(output)
            svg_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, svg_destination)
            render_svg(source, png_destination, width, height)

        render_specimens(plan, plan_path, staging)
        if output.exists():
            raise SystemExit(f"refusing to replace visual handoff created during render: {output}")
        staging.replace(output)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"rasterized custom font artwork into {output}")
    print(f"created {len(promos)} promos in each ratio")
    print("created four factual specimen PNGs")


def render_openpencil(plan: dict[str, Any], plan_path: Path, output: Path) -> None:
    """Use the OpenPencil core bridge, then add the factual specimen sheets."""
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing visual handoff: {output}")
    bridge = Path(__file__).with_name("render_openpencil_font_handoff.mjs")
    if not bridge.is_file():
        raise SystemExit(f"missing OpenPencil render bridge: {bridge}")
    staging = output.with_name(f"{output.name}.staging")
    if staging.exists():
        raise SystemExit(f"refusing to reuse existing staging directory: {staging}")
    try:
        subprocess.run(
            ["node", str(bridge), "--plan", str(plan_path), "--output", str(staging)],
            check=True,
        )
        render_specimens(plan, plan_path, staging)
        if output.exists():
            raise SystemExit(f"refusing to replace visual handoff created during render: {output}")
        staging.replace(output)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    print(f"rendered OpenPencil font artwork into {output}")
    print(f"created {len(plan.get('promos', []))} promos in each ratio")
    print("created four factual specimen PNGs")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"visual plan not found: {args.plan}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid visual plan JSON: {error}")
    if not isinstance(plan, dict):
        raise SystemExit("visual plan root must be a JSON object")
    if plan.get("render_mode") in {"openpencil", "open-pencil"}:
        render_openpencil(plan, args.plan.resolve(), args.output)
    else:
        render_direct(plan, args.plan.resolve(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
