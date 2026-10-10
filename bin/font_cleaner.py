#!/usr/bin/env python3
"""Safely audit a font directory and optionally move confirmed failures aside.

This tool never deletes fonts. By default it is a dry run. With ``--apply``
it moves only fonts that cannot be loaded or have no complete basic Latin
alphabet into a sibling ``Fonts-Trash`` directory, preserving subdirectories.
Embedding flags, missing kerning, and unusual metadata are reported but are
not treated as trash: those may be repairable or intentional.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from fontTools.ttLib import TTFont


FONT_EXTENSIONS = {".ttf", ".otf", ".woff", ".woff2"}
BASIC_LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def audit(path: Path) -> dict:
    """Audit tables/cmap only; never decompile glyph outlines."""
    try:
        with TTFont(path, lazy=True, ignoreDecompileErrors=True) as font:
            cmap = font.getBestCmap() or {}
            missing = [char for char in BASIC_LATIN if ord(char) not in cmap]
            fstype = font["OS/2"].fsType if "OS/2" in font else None
            return {
                "action": "trash" if missing else "keep",
                "reason": f"missing basic Latin: {''.join(missing)}" if missing else "loads and has A-Z/a-z cmap",
                "missing": "".join(missing),
                "fsType": fstype,
                "kern": "kern" in font,
                "GPOS": "GPOS" in font,
            }
    except Exception as error:
        return {"action": "trash", "reason": f"cannot load: {error}", "missing": "", "fsType": None}


def targets(root: Path, trash: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in FONT_EXTENSIONS and trash not in path.parents
    )


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination
    for number in range(2, 10000):
        candidate = destination.with_name(f"{destination.stem}__{number}{destination.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not find a free destination for {destination.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="directory containing fonts to inspect")
    parser.add_argument("--trash-name", default="Fonts-Trash", help="sibling folder name")
    parser.add_argument("--apply", action="store_true", help="move confirmed failures; otherwise report only")
    args = parser.parse_args()
    root = args.directory.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    trash = root.parent / args.trash_name
    results = []
    for path in targets(root, trash):
        result = audit(path)
        result.update(source=str(path), relative=str(path.relative_to(root)))
        results.append(result)
        print(f"{'TRASH' if result['action'] == 'trash' else 'KEEP':5}  {result['relative']}  — {result['reason']}")

    failures = [result for result in results if result["action"] == "trash"]
    print(f"\nScanned {len(results)} font(s); {len(failures)} confirmed failure(s).")
    if not args.apply:
        print(f"Dry run only. Re-run with --apply to move failures into {trash}")
        return 0

    manifest = []
    for result in failures:
        source = Path(result["source"])
        destination = unique_destination(trash / Path(result["relative"]))
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        result["moved_to"] = str(destination)
        manifest.append(result)
    trash.mkdir(parents=True, exist_ok=True)
    (trash / "font-cleaner-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Moved {len(manifest)} font(s) to {trash}.")
    print("Original paths and reasons are recorded in font-cleaner-manifest.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
