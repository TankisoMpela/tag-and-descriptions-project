#!/usr/bin/env python3
"""Report the mechanical situation inside a seller's visuals/New-Images folder.

Prints facts only — counts, ratio classification, name-marked thumbnails,
existing generated state — so an agent can inspect the folder and decide
which processor flags to use. Never writes inside the folder.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from process_final_font_images import (  # noqa: E402
    IMAGE_SUFFIXES,
    MAIN_RATIO,
    SQUARE_RATIO,
    SQUARE_THUMB_MARKERS,
    inspect_ratio,
    ratio_matches,
)


def classify(path: Path) -> dict[str, object]:
    entry: dict[str, object] = {"file": path.name}
    try:
        width, height, ratio = inspect_ratio(path, path.name)
    except SystemExit as error:
        entry["ratio"] = "undecodable"
        entry["error"] = str(error)
        return entry
    entry["width"] = width
    entry["height"] = height
    entry["ratio"] = "3:2" if ratio_matches(ratio, MAIN_RATIO) else (
        "1:1" if ratio_matches(ratio, SQUARE_RATIO) else "unsupported"
    )
    if entry["ratio"] == "1:1":
        entry["name_marked_square_thumbnail"] = any(
            token in path.name.lower() for token in SQUARE_THUMB_MARKERS
        )
    return entry


def generated_state(folder: Path) -> dict[str, object]:
    state: dict[str, object] = {}
    for label, relative in (
        ("source_3x2", "source/3x2"),
        ("source_1x1", "source/1x1"),
        ("main_jpegs", "main"),
        ("square_jpegs", "squares"),
        ("pinterest", "pinterest"),
    ):
        target = folder / relative
        state[label] = len([p for p in target.iterdir() if p.is_file()]) if target.is_dir() else 0
    state["manifest"] = (folder / "final-image-manifest.md").is_file()
    return state


def notes_for(files: list[dict[str, object]]) -> list[str]:
    main = [f for f in files if f["ratio"] == "3:2"]
    squares = [f for f in files if f["ratio"] == "1:1"]
    marked = [f for f in squares if f.get("name_marked_square_thumbnail")]
    if any(f["ratio"] in ("unsupported", "undecodable") for f in files):
        return ["Blockers present: every direct file must be a decodable 3:2 or 1:1 image."]
    if not main:
        return ["No 3:2 files: process_final_font_images.py cannot run (it requires at least one 3:2 file)."]
    if not squares:
        return [
            f"No 1:1 files: run process_final_font_images.py --auto-order --pad-squares "
            f"to derive all {len(main)} square(s) from the 3:2 set (equal white top/bottom padding)."
        ]
    if len(squares) == 1 and marked and len(main) > 1:
        return [
            "One name-marked square thumbnail: run process_final_font_images.py --auto-order "
            f"--pad-squares to keep it and derive {len(main) - 1} supporting square(s) from the 3:2 promos."
        ]
    return [
        f"{len(squares)} 1:1 file(s) supplied: run process_final_font_images.py --auto-order as-is; "
        "no padding is implied and the two counts need not match."
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report facts about a New-Images folder; writes nothing."
    )
    parser.add_argument("folder", type=Path, help="visuals/New-Images folder to inspect")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object instead of text")
    args = parser.parse_args()

    folder = args.folder.expanduser().resolve()
    if not folder.is_dir():
        print(f"Folder not found: {folder}", file=sys.stderr)
        return 1

    direct = sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )
    if not direct:
        print(f"No direct raster images found in {folder}", file=sys.stderr)
        return 1

    files = [classify(path) for path in direct]
    report = {
        "folder": str(folder),
        "direct_images": files,
        "counts": {
            "3:2": sum(1 for f in files if f["ratio"] == "3:2"),
            "1:1": sum(1 for f in files if f["ratio"] == "1:1"),
            "unsupported": sum(1 for f in files if f["ratio"] == "unsupported"),
            "undecodable": sum(1 for f in files if f["ratio"] == "undecodable"),
        },
        "name_marked_square_thumbnails": [
            f["file"] for f in files if f.get("name_marked_square_thumbnail")
        ],
        "generated_state": generated_state(folder),
        "notes": notes_for(files),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"New-Images situation report: {folder}")
    print("")
    print("Direct images (stable filename order = processing order):")
    for entry in files:
        if "width" in entry:
            marker = " [name-marked square thumbnail]" if entry.get("name_marked_square_thumbnail") else ""
            print(f"  {entry['file']}: {entry['width']}x{entry['height']} ({entry['ratio']}){marker}")
        else:
            print(f"  {entry['file']}: UNDECODABLE — {entry.get('error', 'unknown error')}")
    counts = report["counts"]
    print("")
    print(f"Counts: {counts['3:2']} x 3:2, {counts['1:1']} x 1:1, "
          f"{counts['unsupported']} unsupported, {counts['undecodable']} undecodable")
    state = report["generated_state"]
    print("Generated state: " + ", ".join(
        f"{key}={value}" for key, value in state.items()
    ))
    print("")
    for note in report["notes"]:
        print(f"Note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
