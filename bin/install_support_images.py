#!/usr/bin/env python3
"""Copy Agent 27's support images and optional generated thumbnails into Agent 30's input drop."""
from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path,
                        help="Agent 27 prepared_visuals folder")
    parser.add_argument("--output", required=True, type=Path,
                        help="visuals/New-Images input folder")
    parser.add_argument("--include-thumbnails", action="store_true",
                        help="also install Agent 27's four generated images from final-thumbnails/")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_dir():
        raise SystemExit(f"supporting-image source not found: {source}")
    files = {
        "3x2": sorted((source / "supporting" / "3x2").glob("support-*.png")),
        "1x1": sorted((source / "supporting" / "1x1").glob("support-*.png")),
    }
    for ratio, paths in files.items():
        if len(paths) != 12:
            raise SystemExit(f"expected 12 supporting images in {ratio}; found {len(paths)}")
    thumbnails = [
        source / "final-thumbnails" / name
        for name in (
            "thumbnail_main_3x2.png",
            "thumbnail_main_1x1.png",
            "thumbnail_alt_3x2.png",
            "thumbnail_alt_1x1.png",
        )
    ] if args.include_thumbnails else []
    missing = [path for path in thumbnails if not path.is_file()]
    if missing:
        raise SystemExit("missing Agent-27 generated thumbnail(s): " + ", ".join(str(path) for path in missing))
    output.mkdir(parents=True, exist_ok=True)
    installed = 0
    for ratio in ("3x2", "1x1"):
        for original in files[ratio]:
            name = original.stem + ("_1x1" if ratio == "1x1" else "") + original.suffix.lower()
            destination = output / name
            if destination.exists():
                if digest(destination) != digest(original):
                    raise SystemExit(f"refusing to replace a different direct input: {destination}")
                continue
            shutil.copy2(original, destination)
            installed += 1
    for original in thumbnails:
        destination = output / original.name
        if destination.exists():
            if digest(destination) != digest(original):
                raise SystemExit(f"refusing to replace a different direct input: {destination}")
            continue
        shutil.copy2(original, destination)
        installed += 1
    label = "24 support images and four thumbnails" if thumbnails else "all 24 supporting images"
    print(f"[PASS] {label} present in {output} ({installed} newly copied)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
