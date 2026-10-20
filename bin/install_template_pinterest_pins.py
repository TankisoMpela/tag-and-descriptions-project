#!/usr/bin/env python3
"""Install Agent 27's rendered Pinterest template pins into an Agent 13 output."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

from PIL import Image


ACTIVE_TEMPLATES = (
    "hero", "set", "wall", "full_stack", "studio_cover", "specimen_mosaic",
    "initials", "knotband", "scriptorium", "carol", "illuminated_broadside",
    "scribe_gallery", "crest", "bib", "lane", "finish", "timer", "guide",
    "trace", "letter_study", "coffee_roaster", "punk_manifesto", "neon_overprint",
)
MANIFEST_NAME = "pinterest-template-manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(message)


def validate_source(source: Path) -> tuple[dict, list[Path]]:
    manifest_path = source / MANIFEST_NAME
    if not manifest_path.is_file():
        fail(f"missing Agent 27 Pinterest manifest: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid Agent 27 Pinterest manifest: {error}")
    if manifest.get("kind") != "font-template-pinterest-pins":
        fail("Agent 27 Pinterest manifest has an unexpected kind")
    rows = manifest.get("images")
    if manifest.get("template_count") != len(ACTIVE_TEMPLATES) or not isinstance(rows, list) or len(rows) != len(ACTIVE_TEMPLATES):
        fail(f"Agent 27 must provide exactly {len(ACTIVE_TEMPLATES)} active Pinterest template pins")
    files: list[Path] = []
    for index, (row, template) in enumerate(zip(rows, ACTIVE_TEMPLATES), start=1):
        filename = f"pinterest_{index}.jpg"
        if row.get("index") != index or row.get("template") != template or row.get("file") != filename:
            fail(f"Agent 27 Pinterest manifest row {index} must describe {template}/{filename}")
        path = source / filename
        if not path.is_file():
            fail(f"missing Agent 27 Pinterest pin: {path}")
        if path.stat().st_size > 200000 or row.get("bytes") != path.stat().st_size:
            fail(f"Agent 27 Pinterest pin has an invalid size: {path}")
        try:
            with Image.open(path) as image:
                image.load()
                if image.format != "JPEG" or image.size != (1000, 1500):
                    fail(f"Agent 27 Pinterest pin must be a 1000x1500 JPEG: {path}")
        except Exception as error:
            fail(f"cannot decode Agent 27 Pinterest pin {path}: {error}")
        if row.get("sha256") != sha256(path):
            fail(f"Agent 27 Pinterest pin checksum does not match its manifest: {path}")
        files.append(path)
    return manifest, files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Agent 27 prepared_visuals/pinterest")
    parser.add_argument("--output", required=True, type=Path, help="Agent 13 visuals/New-Images/pinterest")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing template pins 1–23")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    target = args.output.expanduser().resolve()
    if not source.is_dir():
        fail(f"Agent 27 Pinterest folder not found: {source}")
    manifest, files = validate_source(source)
    target.mkdir(parents=True, exist_ok=True)
    existing = [p for p in target.iterdir() if p.is_file() and (
        p.name == MANIFEST_NAME or
        ((match := re.fullmatch(r"pinterest_(\d+)\.(?:png|jpe?g)", p.name, re.IGNORECASE))
         and int(match.group(1)) <= len(ACTIVE_TEMPLATES))
    )]
    if existing and not args.overwrite:
        fail("template pins already exist; rerun with --overwrite to replace indexes 1–23")
    if args.overwrite:
        for path in existing:
            path.unlink()
    for source_path in files:
        shutil.copy2(source_path, target / source_path.name)
    shutil.copy2(source / MANIFEST_NAME, target / MANIFEST_NAME)
    _, copied = validate_source(target)
    if any(sha256(source_path) != sha256(target_path) for source_path, target_path in zip(files, copied)):
        fail("copied Pinterest template pins differ from Agent 27's source assets")
    print(f"[PASS] installed {len(files)} template Pinterest pins for {manifest['font_name']}: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
